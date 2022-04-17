from pydantic import BaseModel


class SongDownload(BaseModel):
    data: bytes
    info: dict
