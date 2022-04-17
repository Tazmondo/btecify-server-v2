from pydantic import BaseModel


class SongDownload(BaseModel):
    data: bytes
    thumbdata: bytes
    info: dict


class PlaylistDownload:
    info: dict
    songs: list[SongDownload]


class SongIn(BaseModel):
    title: str
    album: str | None
    duration: int
    extractor: str | None
    weburl: str | None
    thumburl: str | None
    artist: str


class PlaylistIn(BaseModel):
    title: str
    songs: list[SongIn]


class FullSync(BaseModel):
    playlists: list[PlaylistIn]
