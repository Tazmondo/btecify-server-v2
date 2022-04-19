from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic.utils import GetterDict


# To resolve the association table when converting many-to-many into a schema.
def getterMaker(keys: list[str], proxiedObjectName: str):
    class NewGetter(GetterDict):
        def get(self, key: str, default=None) -> Any:
            if key not in keys:
                return getattr(getattr(self._obj, proxiedObjectName), key)
            else:
                return super().get(key, default)

    return NewGetter


class SongDownload(BaseModel):
    data: bytes
    dataext: str
    thumbdata: bytes
    thumbext: str
    info: dict


class PlaylistDownload:
    info: dict
    songs: list[SongDownload]


class Album(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True


class Artist(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True


class PlaylistBase(BaseModel):
    id: int
    title: str


class SongBase(BaseModel):
    id: int
    title: str
    album: Album | None
    duration: float
    extractor: str
    weburl: str
    artist: Artist


class SongPlaylist(PlaylistBase):
    dateadded: datetime

    class Config:
        orm_mode = True
        getter_dict = getterMaker(['dateadded'], 'playlist')


class Song(SongBase):
    playlists: list[SongPlaylist]

    class Config:
        orm_mode = True


# class PlaylistSongGetter(GetterDict):
#     def get(self, key: str, default = None) -> Any:
#         if key in ['dateadded']:
#             return getattr(self._obj.song, key)
#         else:
#             return super().get(key, default)


class PlaylistSong(SongBase):
    dateadded: datetime
    playlists: list[SongPlaylist]

    class Config:
        orm_mode = True
        getter_dict = getterMaker(['dateadded'], 'song')


class Playlist(PlaylistBase):
    songs: list[PlaylistSong] = []

    class Config:
        orm_mode = True


class PlaylistIn(BaseModel):
    title: str
    songs: list[Song]


class SongIn(BaseModel):
    weburl: str
    title: str | None
    album: str | None
    artist: str | None


class ExceptionResponse(BaseModel):
    detail: str


class SongFullSync(BaseModel):
    title: str
    album: str | None
    duration: float
    extractor: str
    weburl: str | None
    thumburl: str | None
    artist: str


class PlaylistFullSync(BaseModel):
    title: str
    songs: list[SongFullSync]


class FullSync(BaseModel):
    playlists: list[PlaylistFullSync]
