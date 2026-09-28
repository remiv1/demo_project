"""Main application for the API frontend."""

import json
import os
import re
from typing import Protocol, cast
from urllib.parse import urlsplit

from flask import Flask, abort, redirect, request, url_for
from flask_sock import Sock
from flask_wtf.csrf import CSRFProtect

from blueprints.user import blueprint as user_blueprint
from blueprints.user.utils import authenticated

from redis import Redis

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
csrf = CSRFProtect(app)
sock = Sock(app)
app.register_blueprint(user_blueprint)
NOTIFICATION_STREAM = "new_event"


@app.get("/")
def index():
    """Oriente vers l'espace utilisateur."""
    return redirect(url_for("user.account"))


class WebSocketSender(Protocol):
    """Interface de diffusion utilisée par Flask-Sock."""

    def send(self, data: str) -> None:
        """Envoie un message à la connexion WebSocket."""


@app.before_request
def protect_events_socket() -> None:
    """Refuse les sockets non autorisées avant la poignée de main."""
    if request.path != "/ws/events":
        return
    if not authenticated():
        abort(403)

    cursor = request.args.get("since")
    if cursor is not None and re.fullmatch(r"\d{1,20}-\d{1,20}", cursor, re.ASCII) is None:
        abort(400)

    origin = request.headers.get("Origin", "")
    if urlsplit(origin).netloc != request.host or urlsplit(origin).scheme not in ("http", "https"):
        abort(403)


@sock.route("/ws/events")
def events(websocket: WebSocketSender) -> None:
    """Diffuse les notifications du Stream depuis le dernier ID reçu."""
    redis_client = Redis(
        host=os.getenv("REDIS_HOST", "redis-streams"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        username=os.environ["REDIS_USERNAME"],
        password=os.environ["REDIS_PASSWORD"],
        decode_responses=True,
    )
    try:
        last_id = request.args.get("since")
        if last_id is None:
            latest = cast(
                list[tuple[str, dict[str, str]]],
                redis_client.xrevrange(NOTIFICATION_STREAM, count=1),
            )
            last_id = latest[0][0] if latest else "0-0"

        while True:
            entries = cast(
                list[tuple[str, list[tuple[str, dict[str, str]]]]],
                redis_client.xread({NOTIFICATION_STREAM: last_id}, count=10, block=5_000),
            )
            for _, messages in entries:
                for message_id, fields in messages:
                    notification = json.loads(fields["payload"])
                    websocket.send(json.dumps({"id": message_id, **notification}))
                    last_id = message_id
    finally:
        redis_client.close()


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
