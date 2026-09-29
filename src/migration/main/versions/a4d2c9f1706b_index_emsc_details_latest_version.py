"""Indexer la sélection de la dernière version de chaque événement."""

from collections.abc import Sequence

from alembic import op


revision: str = "a4d2c9f1706b"  # pylint: disable=C0103
down_revision: str | Sequence[str] | None = "6d941c12a7be"  # pylint: disable=C0103
branch_labels: str | Sequence[str] | None = None  # pylint: disable=C0103
depends_on: str | Sequence[str] | None = None  # pylint: disable=C0103


def upgrade() -> None:
    """Créer l'index utilisé par la recherche de dernière version."""
    op.create_index(  # pylint: disable=E1101
        "ix_emsc_details_latest_version",
        "emsc_details",
        ["emsc_id", "event_datetime", "id"],
        unique=False,
        schema="app_schema",
    )


def downgrade() -> None:
    """Supprimer l'index de sélection de version."""
    op.drop_index(  # pylint: disable=E1101
        "ix_emsc_details_latest_version",
        table_name="emsc_details",
        schema="app_schema",
    )
