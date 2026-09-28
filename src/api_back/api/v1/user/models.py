"""Modèles Pydantic pour les opérations utilisateur."""

from pydantic import BaseModel, EmailStr, Field

class Credentials(BaseModel):
    """
    Identifiants fournis à l'inscription ou à la connexion.
    
    args:
        email (EmailStr): L'adresse email de l'utilisateur.
        password (str): Le mot de passe de l'utilisateur.
    """

    email: EmailStr
    password: str = Field(min_length=12, max_length=256)


class Registration(Credentials):
    """
    Identifiants et nom public du nouveau compte.
    
    args:
        username (str): Le nom public de l'utilisateur.
    """

    username: str = Field(min_length=3, max_length=50)


class OTPCode(BaseModel):
    """
    Code à six chiffres fourni par l'application TOTP.
    
    args:
        code (str): Le code TOTP à vérifier.
    """

    code: str = Field(pattern=r"^\d{6}$")
