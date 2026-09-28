"""Autoriser plusieurs détails par événement EMSC.

Revision ID: 6d941c12a7be
Revises: 35be609db105
"""

from collections.abc import Sequence

from alembic import op


revision: str = "6d941c12a7be"
down_revision: str | Sequence[str] | None = "35be609db105"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Supprime l'unicité d'un événement dans ses détails."""
    op.drop_constraint(
        "emsc_details_emsc_id_key", "emsc_details", schema="app_schema", type_="unique"
    )


def downgrade() -> None:
    """Rétablit l'unicité d'un événement dans ses détails."""
    op.create_unique_constraint(
        "emsc_details_emsc_id_key", "emsc_details", ["emsc_id"], schema="app_schema"
    )