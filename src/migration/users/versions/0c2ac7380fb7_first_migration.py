"""first_migration

Revision ID: 0c2ac7380fb7
Revises: 
Create Date: 2026-09-22 09:32:04.169890
""" # pylint: disable=C0103

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '0c2ac7380fb7'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Appliquer la migration."""
    op.create_table(    # pylint: disable=E1101
        'users',
        sa.Column(
            'id',
            sa.UUID(),
            nullable=False,
            comment="Identifiant unique de l'utilisateur",
        ),
        sa.Column(
            'username',
            sa.String(length=50),
            nullable=False,
            comment="Nom d'utilisateur unique",
        ),
        sa.Column(
            'email',
            sa.String(length=100),
            nullable=False,
            comment="Adresse email unique de l'utilisateur",
        ),
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            comment="Indique si l'utilisateur est actif",
        ),
        sa.Column(
            'nb_failed_logins',
            sa.Integer(),
            nullable=False,
            comment="Nombre de tentatives de connexion échouées",
        ),
        sa.Column(
            'is_locked',
            sa.Boolean(),
            nullable=False,
            comment="Indique si l'utilisateur est verrouillé",
        ),
        sa.Column(
            'permissions',
            sa.String(length=20),
            nullable=False,
            comment="Permissions de l'utilisateur",
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Date de création de l'utilisateur",
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Date de la dernière mise à jour de l'utilisateur",
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
        schema='auth_schema',
    )
    op.create_table(    # pylint: disable=E1101
        'user_sessions',
        sa.Column(
            'id',
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment='Identifiant unique de la session utilisateur',
        ),
        sa.Column(
            'user_id',
            sa.UUID(),
            nullable=False,
            comment="Identifiant de l'utilisateur associé à la session",
        ),
        sa.Column(
            'token_hash',
            sa.String(length=64),
            nullable=False,
            comment='Empreinte SHA-256 du jeton de session unique',
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Date d'expiration absolue de la session",
        ),
        sa.Column(
            'last_accessed_at',
            sa.DateTime(timezone=True),
            nullable=False,
            comment='Date du dernier accès à la session',
        ),
        sa.Column(
            'revoked_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Date de révocation de la session',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            comment='Date de création de la session',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['auth_schema.users.id'],
            ondelete='all, delete-orphan',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
        schema='auth_schema',
    )
    op.create_table(    # pylint: disable=E1101
        'users_password',
        sa.Column(
            'id',
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment='Identifiant unique du mot de passe',
        ),
        sa.Column(
            'user_id',
            sa.UUID(),
            nullable=False,
            comment="Identifiant de l'utilisateur associé",
        ),
        sa.Column(
            'password_hash',
            sa.String(length=255),
            nullable=False,
            comment="Hash du mot de passe de l'utilisateur",
        ),
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            comment='Indique si le mot de passe est actif',
        ),
        sa.Column(
            'change_needed',
            sa.Boolean(),
            nullable=False,
            comment='Indique si le mot de passe doit être changé',
        ),
        sa.Column(
            'from_date',
            sa.DateTime(timezone=True),
            nullable=False,
            comment='Date de début de validité du mot de passe',
        ),
        sa.Column(
            'to_date',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Date de fin de validité du mot de passe',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['auth_schema.users.id'],
            ondelete='all, delete-orphan'
        ),
        sa.PrimaryKeyConstraint('id'),
        schema='auth_schema'
    )


def downgrade() -> None:
    """Annuler la migration."""
    op.drop_table('users_password', schema='auth_schema')    # pylint: disable=E1101
    op.drop_table('user_sessions', schema='auth_schema')    # pylint: disable=E1101
    op.drop_table('users', schema='auth_schema')    # pylint: disable=E1101
