"""Modèles SQLAlchemy communs."""

from common.config.db import BaseMain, BaseUsers

class CommonMixin(BaseMain):
    """Mixin commun pour les modèles SQLAlchemy."""
    __abstract__ = True

    def to_dict(self):
        """Convertit l'instance en dictionnaire."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def from_dict(self, data):
        """Met à jour l'instance à partir d'un dictionnaire."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

class UserMixin(BaseUsers):
    """Mixin pour les modèles utilisateurs SQLAlchemy."""
    __abstract__ = True

    def to_dict(self):
        """Convertit l'instance en dictionnaire."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def from_dict(self, data):
        """Met à jour l'instance à partir d'un dictionnaire."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
