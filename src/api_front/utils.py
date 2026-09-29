"""Décorateurs partagés par les routes de l'API frontend."""

from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from flask import redirect, url_for
from werkzeug.wrappers import Response

from blueprints.user.utils import authenticated


P = ParamSpec("P")
R = TypeVar("R")


def authenticated_required(view: Callable[P, R]) -> Callable[P, R | Response]:
    """
    Protège une route en redirigeant les sessions non authentifiées.

    Args:
        view: La fonction de vue à protéger.

    Returns:
        La fonction de vue protégée.
    """
    @wraps(view)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R | Response:
        if not authenticated():
            return redirect(url_for("user.login"))
        return view(*args, **kwargs)

    return wrapped
