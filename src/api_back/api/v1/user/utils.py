"""Accès exclusif du backend aux secrets et sessions utilisateur."""

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import pyotp
from argon2 import PasswordHasher
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from common.models.sqlalchemy.users import UserOTP, UserSession, Users


COOKIE_NAME = "auth_session"
HASHER = PasswordHasher()
engine = create_engine(URL.create(
    "postgresql+psycopg2",
    username=os.environ.get("POSTGRES_USER_SECURE", "secure"),
    password=os.environ.get("POSTGRES_PASSWORD_SECURE"),
    host=os.environ.get("POSTGRES_HOST", "db-main"),
    database=os.environ.get("POSTGRES_DB_USERS", "emsc_users"),
), pool_pre_ping=True)
new_session = sessionmaker(bind=engine, expire_on_commit=False)


def now() -> datetime:
    """Retourne l'heure UTC courante."""
    return datetime.now(timezone.utc)


def encrypt_secret(secret: str) -> str:
    """Chiffre le secret TOTP avant persistance."""
    return Fernet(os.environ["OTP_ENCRYPTION_KEY"].encode()).encrypt(secret.encode()).decode()


def decrypt_secret(otp: UserOTP) -> str:
    """Déchiffre le secret TOTP dans le backend uniquement."""
    return Fernet(os.environ["OTP_ENCRYPTION_KEY"].encode()).decrypt(
        otp.secret_encrypted.encode()
    ).decode()


def verify_code(otp: UserOTP, code: str) -> bool:
    """Vérifie un code TOTP sans accepter deux fois le même compteur."""
    totp = pyotp.TOTP(decrypt_secret(otp))
    current = int(now().timestamp()) // totp.interval
    for counter in (current - 1, current, current + 1):
        if counter > (otp.last_counter if otp.last_counter is not None else -1):
            if secrets.compare_digest(totp.at(counter * totp.interval), code):
                otp.last_counter = counter
                return True
    return False


def token_hash(token: str) -> str:
    """Calcule l'empreinte persistée du jeton opaque."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: Users, verified: bool = False) -> str:
    """Crée un jeton aléatoire, dont seule l'empreinte est conservée en base."""
    token = secrets.token_urlsafe(32)
    db.add(UserSession(
        user_id=user.id,
        token_hash=token_hash(token),
        expires_at=now() + timedelta(minutes=10 if not verified else 60 * 24),
        verified_at=now() if verified else None,
    ))
    return token


def get_session(db: Session, token: str | None) -> UserSession | None:
    """Retrouve une session valide à partir du cookie transmis sans décodage."""
    if not token:
        return None
    entry = db.query(UserSession).filter_by(token_hash=token_hash(token)).first()
    if entry is None or entry.revoked_at is not None:
        return None
    if entry.expires_at <= now():
        return None
    return entry
