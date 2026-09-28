"""Pages et formulaires htmx des comptes utilisateur."""

from httpx import Response as HTTPResponse
from flask import Blueprint, Response, abort, redirect, render_template, request, url_for
from werkzeug.wrappers import Response as WerkzeugResponse

from .utils import authenticated, call_backend, forward_cookie, qr_code_png


blueprint = Blueprint("user", __name__, url_prefix="/user")
FEEDBACK_TEMPLATE = "user/_feedback.html"
ENROLL_PAGE = "user.enroll_page"
LOGIN_PAGE = "user.login_page"


@blueprint.after_request
def prevent_auth_cache(response: WerkzeugResponse) -> WerkzeugResponse:
    """Empêche la mise en cache des pages et des secrets d'authentification."""
    response.headers["Cache-Control"] = "no-store"
    return response


def form_error(result: object, fallback: str) -> str:
    """Retourne un message d'erreur sans divulguer de détails internes."""
    if isinstance(result, HTTPResponse) and result.status_code in (401, 409, 422):
        return fallback
    return "Service temporairement indisponible."


@blueprint.get("/register")
def register_page() -> str:
    """Affiche le formulaire de création de compte."""
    return render_template("user/register.html")


@blueprint.post("/register")
def register() -> Response | str | WerkzeugResponse:
    """Transmet la création du compte au back."""
    result = call_backend("POST", "register", {
        "username": request.form.get("username", ""),
        "email": request.form.get("email", ""),
        "password": request.form.get("password", ""),
    })
    if result.status_code != 201:
        return render_template(
            FEEDBACK_TEMPLATE,
            message=form_error(
                result,
                "Compte indisponible ou données invalides.",
            )
        )
    if request.headers.get("HX-Request") != "true":
        response = redirect(url_for(ENROLL_PAGE))
        forward_cookie(result, response)
        return response
    response = Response(status=204)
    forward_cookie(result, response)
    response.headers["HX-Redirect"] = url_for(ENROLL_PAGE)
    return response


@blueprint.get("/login")
def login_page() -> str:
    """Affiche la connexion par mot de passe."""
    return render_template("user/login.html")


@blueprint.post("/login")
def login() -> Response | str | WerkzeugResponse:
    """Démarre une session provisoire après vérification du mot de passe."""
    result = call_backend("POST", "login", {
        "email": request.form.get("email", ""),
        "password": request.form.get("password", ""),
    })
    if result.status_code != 200:
        return render_template(
            FEEDBACK_TEMPLATE,
            message=form_error(
                result,
                "Identifiants invalides.",
            )
        )
    destination = url_for(
        ENROLL_PAGE if result.json()["next"] == "enroll" else "user.verify_page"
    )
    if request.headers.get("HX-Request") != "true":
        response = redirect(destination)
        forward_cookie(result, response)
        return response
    response = Response(status=204)
    forward_cookie(result, response)
    response.headers["HX-Redirect"] = destination
    return response


@blueprint.get("/enroll")
def enroll_page() -> str:
    """Affiche l'activation TOTP sur la session provisoire."""
    return render_template("user/enroll.html")


@blueprint.post("/enroll")
def enroll() -> str:
    """Demande au back l'URI TOTP et l'affiche sous forme de QR code."""
    result = call_backend("POST", "enroll")
    if result.status_code != 200:
        return render_template(
            FEEDBACK_TEMPLATE,
            message="Enrôlement indisponible. Reconnectez-vous.",
        )
    enrollment = result.json()
    context = {"secret": enrollment["secret"], "qr_png": qr_code_png(enrollment["uri"])}
    if request.headers.get("HX-Request") != "true":
        return render_template("user/enroll.html", **context)
    return render_template("user/_secret.html", **context)


@blueprint.get("/verify")
def verify_page() -> str:
    """Affiche la validation TOTP après mot de passe ou enrôlement."""
    return render_template("user/verify.html")


@blueprint.post("/verify")
def verify() -> Response | str | WerkzeugResponse:
    """Valide le code auprès du back et relaie le cookie renouvelé."""
    result = call_backend("POST", "verify", {"code": request.form.get("code", "")})
    if result.status_code != 200:
        return render_template(
            FEEDBACK_TEMPLATE,
            message="Code invalide ou session expirée.",
        )
    if request.headers.get("HX-Request") != "true":
        response = redirect(url_for("user.account"))
        forward_cookie(result, response)
        return response
    response = Response(status=204)
    forward_cookie(result, response)
    response.headers["HX-Redirect"] = url_for("user.account")
    return response


@blueprint.get("/account")
def account() -> Response | str | WerkzeugResponse:
    """N'affiche la page privée qu'après validation backend de la session."""
    if not authenticated():
        return redirect(url_for(LOGIN_PAGE))
    return render_template("user/account.html")


@blueprint.post("/logout")
def logout() -> Response | WerkzeugResponse:
    """Révoque la session côté backend puis relaie l'effacement du cookie."""
    result = call_backend("POST", "logout")
    if result.status_code != 200:
        abort(503)
    if request.headers.get("HX-Request") != "true":
        response = redirect(url_for(LOGIN_PAGE))
        forward_cookie(result, response)
        return response
    response = Response(status=204)
    forward_cookie(result, response)
    response.headers["HX-Redirect"] = url_for(LOGIN_PAGE)
    return response
