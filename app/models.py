from sqlalchemy import Table, Column, ForeignKey, String, Integer, LargeBinary, Boolean
from sqlalchemy.orm import relationship

from .db import Base

playlist_song_table = Table(
    'playlist_song', Base.metadata,
    Column('song_id', ForeignKey('Song.id'), primary_key=True),
    Column('playlist_id', ForeignKey('Playlist.id'), primary_key=True)
)


class Song(Base):
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    album = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    extractor = Column(String, nullable=True)
    weburl = Column(String, nullable=True)

    disabled = Column(Boolean, nullable=False, default=False)

    data = Column(LargeBinary, nullable=True)
    thumbnail = Column(LargeBinary, nullable=True)

    artist_id = Column(Integer, ForeignKey('Artist.id'))
    artist = relationship("Artist", back_populates="songs")

    playlists = relationship('Playlist', secondary=playlist_song_table, back_populates='songs')


class Artist(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    songs = relationship("Song", back_populates="artist")


class Playlist(Base):
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    thumbnail = Column(LargeBinary, nullable=True)

    songs = relationship('Song', secondary=playlist_song_table, back_populates='playlists')


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    admin = Column(Boolean, default=False)
