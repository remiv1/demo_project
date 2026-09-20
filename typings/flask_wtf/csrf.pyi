""""CSRF protection for Flask-WTF stub file."""
from typing import Any


class CSRFProtect:
    """CSRF protection for Flask-WTF."""
    def __init__(self, app: Any | None = None) -> None: ... # pylint: disable=W0613
    def init_app(self, app: Any) -> None: ...# pylint: disable=C0116, W0613
    def exempt(self, view: Any) -> Any: ... # pylint: disable=C0116, W0613
