from os import environ

from sqlalchemy import Column, ForeignKey, String, Integer, LargeBinary, Boolean, Float, DateTime
from sqlalchemy.orm import relationship

from .db import Base, engine


class PlaylistSong(Base):
    __tablename__ = "playlist_song"
    song_id = Column(Integer, ForeignKey('song.id'), primary_key=True)
    playlist_id = Column(Integer, ForeignKey('playlist.id'), primary_key=True)
    dateadded = Column(DateTime, nullable=False)

    playlist = relationship("Playlist", back_populates="songs")
    song = relationship("Song", back_populates="playlists")


class Song(Base):
    __tablename__ = "song"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    duration = Column(Float, nullable=True)

    disabled = Column(Boolean, nullable=False, default=False)

    extractor = Column(String, nullable=True)
    data_uuid = Column(String, nullable=True)
    dataext = Column(String, nullable=True)
    weburl = Column(String, nullable=True, unique=True)

    thumb_id = Column(String, ForeignKey('thumbnail.id'), nullable=True)
    thumbnail = relationship("Thumbnail")

    artist_id = Column(Integer, ForeignKey('artist.id'))
    artist = relationship("Artist", back_populates="songs")

    album_id = Column(Integer, ForeignKey("album.id"), nullable=True)
    album = relationship('Album', back_populates="songs")

    playlists = relationship('PlaylistSong', back_populates='song')


class Thumbnail(Base):
    __tablename__ = "thumbnail"
    id = Column(Integer, primary_key=True)
    hash = Column(String, nullable=False)
    data_uuid = Column(String, nullable=False)
    ext = Column(String, nullable=False)


class Album(Base):
    __tablename__ = "album"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    # Commented until i have a way of differentiating between albums with the same name
    # artist_id = Column(Integer, ForeignKey('artist.id'))
    # artist = relationship("Artist", back_populates="albums")

    songs = relationship("Song", back_populates="album")


class Artist(Base):
    __tablename__ = "artist"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, unique=True)

    songs = relationship("Song", back_populates="artist")
    # albums = relationship("Album", back_populates="artist")


class Playlist(Base):
    __tablename__ = "playlist"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    thumbnail = Column(LargeBinary, nullable=True)

    songs = relationship('PlaylistSong', back_populates='playlist', cascade="all, delete, delete-orphan")


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    admin = Column(Boolean, default=False)


if environ.get('testdb'):
    Base.metadata.create_all(bind=engine)
