"""phone number added

Revision ID: e29bcf60eb3b
Revises: 
Create Date: 2026-02-08 16:20:55.787213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e29bcf60eb3b' # revizyon gerçekleştirmek için bunu kullanacağız
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))


def downgrade() -> None:
    # op.drop_column('users', 'phone_number')
    pass