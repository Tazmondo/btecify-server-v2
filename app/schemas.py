from pydantic import BaseModel


class SongDownload(BaseModel):
    data: bytes
    thumbdata: bytes
    info: dict


class PlaylistDownload:
    info: dict
    songs: list[SongDownload]
