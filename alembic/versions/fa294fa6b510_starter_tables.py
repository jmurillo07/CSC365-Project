"""create starter tables

Revision ID: fa294fa6b510
Revises: 
Create Date: 2023-05-22 07:19:30.388867

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa294fa6b510'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'fighters',
        sa.Column('fighter_id', sa.Integer, sa.Identity(), primary_key=True, nullable=False),
        sa.Column('first_name', sa.Text),
        sa.Column('last_name', sa.Text),
        sa.Column('height', sa.Integer),
        sa.Column('reach', sa.Integer),
        sa.Column('stance_id', sa.Integer, sa.ForeignKey('stances.id')),
    )

    # Enumeration table
    stances_table = op.create_table(
        'stances',
        sa.Column('id', sa.Integer, sa.Identity(), primary_key=True, nullable=False),
        sa.Column('stance', sa.Text, nullable=False),
    )
    op.bulk_insert(
        stances_table,
        [
            {'stance': 'Orthodox'},
            {'stance': 'Southpaw'},
            {'stance': 'Switch'},
        ],
    )

    op.create_table(
        'fighter_stats',
        sa.Column('stats_id', sa.BigInteger, sa.Identity(), primary_key=True, nullable=False),
        sa.Column('kd', sa.Integer, server_default='0'),
        sa.Column('strikes', sa.Integer, server_default='0'),
        sa.Column('td', sa.Integer, server_default='0'),
        sa.Column('sub', sa.Integer, server_default='0'),
        sa.Column('weight', sa.Integer),
        sa.Column('fighter_id', sa.Integer, sa.ForeignKey('fighters.fighter_id'), nullable=False),
    )

    # Enumeration table
    victory_methods_table = op.create_table(
        'victory_methods',
        sa.Column('id', sa.Integer, sa.Identity(), primary_key=True, nullable=False),
        sa.Column('method', sa.Text),
    )
    op.bulk_insert(
        victory_methods_table,
        [
            {'method': 'SUB'},
            {'method': 'KO/TKO'},
            {'method': 'S-Dec'},
            {'method': 'M-Dec'},
            {'method': 'U-Dec'},
            {'method': 'CNC'},
            {'method': 'DQ'},
        ],
    )

    op.create_table(
        'fights',
        sa.Column('fight_id', sa.BigInteger, sa.Identity(), primary_key=True, nullable=False),
        sa.Column('event_id', sa.Integer, sa.ForeignKey('events.event_id')),
        sa.Column('result', sa.Integer),
        sa.Column('fighter1_id', sa.Integer, sa.ForeignKey('fighters.fighter_id'), nullable=False),
        sa.Column('fighter2_id', sa.Integer, sa.ForeignKey('fighters.fighter_id'), nullable=False),
        sa.Column('method_of_vic', sa.Integer, sa.ForeignKey('victory_methods.id')),
        sa.Column('round_num', sa.Integer, sa.CheckConstraint('round_num>=1 AND round_num<=5'), nullable=False),
        sa.Column('round_time', sa.Text),
        sa.Column('stats1_id', sa.Integer, sa.ForeignKey('fighter_stats.stats_id'), nullable=False),
        sa.Column('stats2_id', sa.Integer, sa.ForeignKey('fighter_stats.stats_id'), nullable=False),
    )

    op.create_table(
        'events',
        sa.Column('event_id', sa.Integer, sa.Identity(), primary_key=True, nullable=False),
        sa.Column('event_name', sa.Text, server_default=''),
        sa.Column('event_date', sa.DateTime),
        sa.Column('venue_id', sa.Integer, sa.ForeignKey('venue.venue_id')),
        sa.Column('attendance', sa.Integer),
    )

    op.create_table(
        'venue',
        sa.Column('venue_id', sa.Integer, sa.Identity(), primary_key=True, nullable=False),
        sa.Column('venue_name', sa.Text)
    )

    op.create_table(
        'predictions',
        sa.Column('prediction_id', sa.Integer, sa.Identity(), primary_key=True, nullable=False),
        sa.Column('fighter_id', sa.Integer, sa.ForeignKey('fighters_fighter_id'), nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.user_id'), nullable=False),
    )

    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer, sa.Identity(), primary_key=True, nullable=False),
        sa.Column('username', sa.Text, nullable=False),
    )


def downgrade() -> None:
    op.drop_table('fighters')
    op.drop_table('stances')
    op.drop_table('fighter_stats')
    op.drop_table('victory_methods')
    op.drop_table('fights')
    op.drop_table('events')
    op.drop_table('venue')
    op.drop_table('predictions')
    op.drop_table('users')
