"""Page cartographique et relais privé du GeoJSON historique."""

import os
from calendar import monthrange
from datetime import datetime, timezone

import httpx
from flask import Blueprint, Response, jsonify, render_template, request
from werkzeug.wrappers import Response as WerkzeugResponse

from blueprints.user.utils import BACKEND_URL
from utils import authenticated_required


blueprint = Blueprint("map", __name__, url_prefix="/map")


@blueprint.after_request
def prevent_cache(response: WerkzeugResponse) -> WerkzeugResponse:
    """Empêche la mise en cache des pages et données privées."""
    response.headers["Cache-Control"] = "no-store"
    return response


@blueprint.get("")
@authenticated_required
def page() -> str:
    """Affiche la carte sans charger les événements avant confirmation."""
    end = datetime.now(timezone.utc).date()
    month = (end.month - 2) % 12 + 1
    year = end.year - (end.month == 1)
    start = end.replace(year=year, month=month, day=min(end.day, monthrange(year, month)[1]))
    if start.day != end.day:
        start = end.replace(day=1)
    return render_template(
        "map/index.html", start=start.isoformat(), end=end.isoformat(),
        tile_url=os.getenv("MAP_TILE_URL", "https://tile.openstreetmap.org/{z}/{x}/{y}.png"),
        tile_attribution=os.getenv(
            "MAP_TILE_ATTRIBUTION",
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        ),
    )


@blueprint.get("/events")
def events() -> Response:
    """Relaie la période et le cookie au backend qui vérifie la session TOTP."""
    key = os.environ.get("AUTH_INTERNAL_KEY")
    if not key:
        response = jsonify(error="Service temporairement indisponible.")
        response.status_code = 503
        return response
    try:
        with httpx.Client(timeout=60.0) as client:
            result = client.get(
                f"{BACKEND_URL}/api/v1/events",
                params={"start": request.args.get("start", ""), "end": request.args.get("end", "")},
                headers={"X-Frontend-Key": key, "Cookie": request.headers.get("Cookie", "")},
            )
        if result.status_code == 200:
            return Response(result.content, mimetype="application/geo+json")
        status = result.status_code if result.status_code in (401, 403, 422) else 503
    except httpx.RequestError:
        status = 503
    messages = {
        401: "Session expirée. Reconnectez-vous.",
        403: "Authentification complète requise.",
        422: "Période invalide : choisissez au maximum un mois calendaire glissant.",
        503: "Service temporairement indisponible.",
    }
    response = jsonify(error=messages[status])
    response.status_code = status
    return response
