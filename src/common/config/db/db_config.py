"""Configuration de la connexion à la base de données."""

from os import getenv
from enum import Enum

CASCADE_OPTION = "all, delete-orphan"

class DatabaseUsage(Enum):
    """Types d'utilisation de la base de données."""
    MAIN = "main"
    USERS = "users"

class DatabaseConfig:
    """
    Classe de configuration de la base de données.
    
    Attributs:
        - db_name (str): Nom de la base de données.
        - user_db (str): Nom de l'utilisateur de la base de données.
        - __user_password (str): Mot de passe de l'utilisateur de la base de données.
        - host (str): Hôte de la base de données.
        - port (str): Port de la base de données.
    
    Paramètres:
        - used_for (DatabaseUsage): Indique l'utilisation prévue de la base de données
          (principale ou utilisateurs).
    
    Méthodes:
        - get_url(safe_pass: str | None=None) -> str: Retourne l'URL de connexion à la base
          de données.
        - get_user_password() -> str: Retourne le mot de passe de l'utilisateur de la base
          de données (à n'utiliser que pour le débogage).
        - set_user_password(new_password: str) -> None: Modifie le mot de passe de l'utilisateur
          de la base de données (à n'utiliser que pour le débogage).
    """

    def __init__(self, used_for: DatabaseUsage) -> None:
        if used_for == DatabaseUsage.MAIN:
            self.db_name = getenv('POSTGRES_DB_MAIN', 'main_db')
            self.user_db = getenv('POSTGRES_USER_APP', 'user')
            self.__user_password = getenv('POSTGRES_PASSWORD_APP', 'password')
        elif used_for == DatabaseUsage.USERS:
            self.db_name = getenv('POSTGRES_DB_USERS', 'users_db')
            self.user_db = getenv('POSTGRES_USER_SECURE', 'user')
            self.__user_password = getenv('POSTGRES_PASSWORD_SECURE', 'password')
        self.host = getenv('DB_HOST', 'localhost')
        self.port = getenv('DB_PORT', '5432')

    def get_url(self, safe_pass: str | None=None) -> str:
        """Retourne l'URL de connexion à la base de données principale.

        Si le mot de passe sécurisé est fourni et correct, retourne l'URL complète avec le
        mot de passe réel sinon, retourne l'URL avec le mot de passe masqué.

        Args:
            safe_pass (str | None): Mot de passe sécurisé pour obtenir l'URL complète.

        Returns:
            str: URL de connexion à la base de données.
        """
        if safe_pass == getenv('SAFEPASS') and safe_pass is not None:
            return (f'postgresql://{self.user_db}:{self.__user_password}'
                    f'@{self.host}:{self.port}/{self.db_name}')
        return (f'postgresql://{self.user_db}:REDACTED'
                f'@{self.host}:{self.port}/{self.db_name}')

    def get_user_password(self) -> str:
        """Retourne le mot de passe de l'utilisateur de la base de données.
        A n'utiliser que pour le débogage.
        
        Returns:
            str: Mot de passe de l'utilisateur de la base de données.
        """
        return self.__user_password

    def set_user_password(self, new_password: str) -> None:
        """Modifie le mot de passe de l'utilisateur de la base de données.
        A n'utiliser que pour le débogage.

        Args:
            new_password (str): Nouveau mot de passe de l'utilisateur de la base de données.

        Returns:
            None
        """
        self.__user_password = new_password
