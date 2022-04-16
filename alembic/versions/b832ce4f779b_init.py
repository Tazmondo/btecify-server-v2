"""init

Revision ID: b832ce4f779b
Revises: 
Create Date: 2022-04-16 19:28:18.262918

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b832ce4f779b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Artist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_Artist_id'), 'Artist', ['id'], unique=False)
    op.create_table('Playlist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('thumbnail', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_Playlist_id'), 'Playlist', ['id'], unique=False)
    op.create_table('User',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('admin', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_User_id'), 'User', ['id'], unique=False)
    op.create_table('Song',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('album', sa.String(), nullable=True),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('extractor', sa.String(), nullable=True),
    sa.Column('weburl', sa.String(), nullable=True),
    sa.Column('disabled', sa.Boolean(), nullable=False),
    sa.Column('data', sa.LargeBinary(), nullable=True),
    sa.Column('thumbnail', sa.LargeBinary(), nullable=True),
    sa.Column('artist_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['artist_id'], ['Artist.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_Song_id'), 'Song', ['id'], unique=False)
    op.create_table('playlist_song',
    sa.Column('song_id', sa.Integer(), nullable=False),
    sa.Column('playlist_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['playlist_id'], ['Playlist.id'], ),
    sa.ForeignKeyConstraint(['song_id'], ['Song.id'], ),
    sa.PrimaryKeyConstraint('song_id', 'playlist_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('playlist_song')
    op.drop_index(op.f('ix_Song_id'), table_name='Song')
    op.drop_table('Song')
    op.drop_index(op.f('ix_User_id'), table_name='User')
    op.drop_table('User')
    op.drop_index(op.f('ix_Playlist_id'), table_name='Playlist')
    op.drop_table('Playlist')
    op.drop_index(op.f('ix_Artist_id'), table_name='Artist')
    op.drop_table('Artist')
    # ### end Alembic commands ###
