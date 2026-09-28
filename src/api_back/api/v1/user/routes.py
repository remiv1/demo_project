"""Inscription, identification et validation TOTP côté backend."""

import os
from secrets import compare_digest

import pyotp
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from common.models.sqlalchemy.users import UserOTP, UserSession, Users, UsersPassword

from .utils import (
    COOKIE_NAME,
    HASHER,
    create_session,
    encrypt_secret,
    get_session,
    new_session,
    now,
    verify_code,
    decrypt_secret,
)


router = APIRouter(prefix="/user", tags=["user"])


class Credentials(BaseModel):
    """Identifiants fournis à l'inscription ou à la connexion."""

    email: EmailStr
    password: str = Field(min_length=12, max_length=256)


class Registration(Credentials):
    """Identifiants et nom public du nouveau compte."""

    username: str = Field(min_length=3, max_length=50)


class OTPCode(BaseModel):
    """Code à six chiffres fourni par l'application TOTP."""

    code: str = Field(pattern=r"^\d{6}$")


def database():
    """Ouvre une session SQL pour une requête puis la ferme."""
    with new_session() as db:
        yield db


def internal_key(x_frontend_key: str | None = Header(default=None)) -> None:
    """Réserve les routes d'authentification au proxy Flask interne."""
    expected = os.environ.get("AUTH_INTERNAL_KEY", "")
    if not expected or not x_frontend_key:
        raise HTTPException(status_code=503, detail="Authentification interne non configurée")
    if not compare_digest(x_frontend_key, expected):
        raise HTTPException(status_code=403, detail="Accès refusé")


def set_cookie(response: Response, token: str) -> None:
    """Envoie un cookie de session opaque au navigateur via Flask."""
    response.set_cookie(
        COOKIE_NAME, token, httponly=True, samesite="lax",
        secure=os.environ.get("AUTH_COOKIE_SECURE", "true").lower() == "true",
        max_age=86400, path="/",
    )


def current_session(db: Session, token: str | None) -> UserSession:
    """Exige une session temporaire ou pleinement validée."""
    entry = get_session(db, token)
    if entry is None:
        raise HTTPException(status_code=401, detail="Session absente ou expirée")
    return entry


@router.post(
    "/register",
    dependencies=[Depends(internal_key)],
    status_code=201,
    responses={
        409: {"description": "Compte indisponible"},
    }
)
def register(
    data: Registration,
    response: Response,
    db: Session = Depends(database)
) -> dict[str, str]:
    """Crée le compte et une session provisoire exigeant l'enrôlement TOTP."""
    user = Users(username=data.username.strip(), email=str(data.email).lower(), permissions="basic")
    try:
        db.add(user)
        db.flush()
        db.add(UsersPassword(user_id=user.id, password_hash=HASHER.hash(data.password)))
        token = create_session(db, user)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Compte indisponible") from error
    set_cookie(response, token)
    return {"next": "enroll"}


@router.post(
    "/login",
    dependencies=[Depends(internal_key)],
    responses={
        401: {"description": "Identifiants invalides"},
    }
)
def login(data: Credentials, response: Response, db: Session = Depends(database)) -> dict[str, str]:
    """Contrôle le mot de passe sans authentifier la session avant TOTP."""
    user = db.query(Users).filter(Users.email == str(data.email).lower()).first()
    password = None if user is None else db.query(UsersPassword).filter_by(
        user_id=user.id, is_active=True
    ).first()
    if user is None or password is None or not user.is_active or user.is_locked:
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    try:
        HASHER.verify(password.password_hash, data.password)
    except (VerifyMismatchError, VerificationError) as error:
        raise HTTPException(status_code=401, detail="Identifiants invalides") from error
    token = create_session(db, user)
    db.commit()
    set_cookie(response, token)
    otp = db.query(UserOTP).filter_by(user_id=user.id).first()
    return {"next": "verify" if otp and otp.enabled else "enroll"}


@router.post(
    "/enroll",
    dependencies=[Depends(internal_key)],
    responses={
        401: {"description": "Session absente"},
        403: {"description": "Enrôlement refusé"},
    }
)
def enroll(
    response: Response, auth_session: str | None = Cookie(default=None),
    db: Session = Depends(database),
) -> dict[str, str]:
    """Émet une seule fois le secret d'enrôlement pour une session provisoire."""
    entry = current_session(db, auth_session)
    if entry.verified_at is not None:
        raise HTTPException(status_code=403, detail="Session déjà validée")
    user = db.get(Users, entry.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Session absente ou expirée")
    otp = db.query(UserOTP).filter_by(user_id=entry.user_id).first()
    if otp and otp.enabled:
        raise HTTPException(status_code=403, detail="TOTP déjà activé")
    if otp is None:
        secret = pyotp.random_base32()
        db.add(UserOTP(user_id=entry.user_id, secret_encrypted=encrypt_secret(secret)))
        db.commit()
    else:
        secret = decrypt_secret(otp)
    response.headers["Cache-Control"] = "no-store"
    return {"secret": secret, "uri": pyotp.TOTP(secret).provisioning_uri(
        name=user.email, issuer_name="Demo Project"
    )}


@router.post(
    "/verify",
    dependencies=[Depends(internal_key)],
    responses={
        401: {"description": "Session ou code invalide"},
        403: {"description": "Session déjà validée"}
    }
)
def verify(
    data: OTPCode, response: Response, auth_session: str | None = Cookie(default=None),
    db: Session = Depends(database),
) -> dict[str, str]:
    """Active TOTP et remplace la session provisoire par une session validée."""
    entry = current_session(db, auth_session)
    if entry.verified_at is not None:
        raise HTTPException(status_code=403, detail="Session déjà validée")
    otp = db.query(UserOTP).filter_by(user_id=entry.user_id).with_for_update().first()
    if otp is None or not verify_code(otp, data.code):
        raise HTTPException(status_code=401, detail="Code invalide")
    otp.enabled = True
    entry.revoked_at = now()
    user = db.get(Users, entry.user_id)
    token = create_session(db, user, verified=True)
    db.commit()
    set_cookie(response, token)
    return {"next": "account"}


@router.get("/session", dependencies=[Depends(internal_key)])
def session_status(
    auth_session: str | None = Cookie(default=None), db: Session = Depends(database),
) -> dict[str, bool]:
    """Indique si la session en base est pleinement authentifiée."""
    entry = get_session(db, auth_session)
    return {"authenticated": bool(entry and entry.verified_at is not None)}


@router.post("/logout", dependencies=[Depends(internal_key)])
def logout(
    response: Response, auth_session: str | None = Cookie(default=None),
    db: Session = Depends(database),
) -> dict[str, bool]:
    """Révoque la session en base et efface le cookie navigateur."""
    entry = get_session(db, auth_session)
    if entry is not None:
        entry.revoked_at = now()
        db.commit()
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"authenticated": False}
