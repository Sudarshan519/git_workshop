"""added topics and asked_questions

Revision ID: 771199d08a08
Revises: b66aa7f8b9e9
Create Date: 2025-07-15 15:48:11.766322

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '771199d08a08'
down_revision: Union[str, Sequence[str], None] = 'b66aa7f8b9e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_sessions', sa.Column('current_topic_index', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_sessions', 'current_topic_index')
    # ### end Alembic commands ###
