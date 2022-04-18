from pydantic import BaseModel


class SongDownload(BaseModel):
    data: bytes
    thumbdata: bytes
    info: dict


class PlaylistDownload:
    info: dict
    songs: list[SongDownload]


class Song(BaseModel):
    title: str
    album: str | None
    duration: float
    extractor: str
    weburl: str | None
    thumburl: str | None
    artist: str


class PlaylistIn(BaseModel):
    title: str
    songs: list[Song]


class FullSync(BaseModel):
    playlists: list[PlaylistIn]
