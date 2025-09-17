"""rename url_foto to imagen_path in products table

Revision ID: 9fb929e82cdc
Revises: 83c1c173c069
Create Date: 2025-09-08 20:54:38.798420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fb929e82cdc'
down_revision: Union[str, Sequence[str], None] = '83c1c173c069'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename url_foto column to imagen_path to preserve existing data
    op.alter_column('products', 'url_foto', new_column_name='imagen_path')


def downgrade() -> None:
    """Downgrade schema."""
    # Rename imagen_path column back to url_foto
    op.alter_column('products', 'imagen_path', new_column_name='url_foto')
