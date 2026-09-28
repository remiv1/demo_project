"""Passerelle HTTP vers le backend d'authentification."""

import base64
import os
from io import BytesIO

import httpx
import qrcode
from flask import request
from werkzeug.wrappers import Response


BACKEND_URL = os.environ.get("API_BACK_URL", "http://api-back:8000")


def qr_code_png(uri: str) -> str:
    """Encode l'URI TOTP en QR code PNG sans service externe.

    Args:
        uri: URI d'enrôlement fournie par le backend.

    Returns:
        Image PNG encodée en base64 pour l'affichage local.
    """
    qr = qrcode.QRCode(border=4, box_size=8)
    qr.add_data(uri)
    qr.make(fit=True)
    buffer = BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buffer, kind="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def call_backend(method: str, path: str, data: dict[str, str] | None = None) -> httpx.Response:
    """Transmet la requête au back sans interpréter le cookie de session."""
    key = os.environ.get("AUTH_INTERNAL_KEY")
    if not key:
        return httpx.Response(status_code=503)
    try:
        with httpx.Client(timeout=5.0) as client:
            return client.request(
                method, f"{BACKEND_URL}/api/v1/user/{path}",
                json=data,
                headers={"X-Frontend-Key": key, "Cookie": request.headers.get("Cookie", "")},
            )
    except httpx.RequestError:
        return httpx.Response(status_code=503)


def forward_cookie(source: httpx.Response, target: Response) -> None:
    """Relaie le Set-Cookie opaque du back sans lire sa valeur."""
    for cookie in source.headers.get_list("set-cookie"):
        target.headers.add("Set-Cookie", cookie)


def authenticated() -> bool:
    """Demande au backend si le cookie correspond à une session TOTP validée."""
    result = call_backend("GET", "session")
    return result.status_code == 200 and result.json().get("authenticated") is True
