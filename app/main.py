import io

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from yt_dlp.utils import DownloadError

import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.db import SessionLocal

app = FastAPI()


# Dependency
def getdb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def getSong(songid: int, db: Session):
    dbsong: models.Song = db.query(models.Song).get(songid)
    if not dbsong:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Song not found")
    return dbsong


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get('/src/{songid}', responses={
    200: {
        "content": {"audio/{requested data extension}": {}},
        "description": "Stream back the requested song."
    }
})
async def getSongSource(songid: int, db: Session = Depends(getdb)):
    dbsong = getSong(songid, db)
    if dbsong.disabled:
        raise HTTPException(status.HTTP_410_GONE, "Song is disabled due to lack of a source.")

    if not dbsong.data:
        try:
            await crud.getSongSource(dbsong, db)
        except DownloadError as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Could not download", e)

    return StreamingResponse(io.BytesIO(dbsong.data), media_type=f"audio/{dbsong.dataext}")


@app.get('/thumb/{songid}')
async def getSongThumb(songid: int, db: Session = Depends(getdb)):
    dbsong = getSong(songid, db)

    if not dbsong.thumbnail:
        pass


@app.post('/song')
async def addSong(song: schemas.Song):
    pass


@app.post('/fullsync')
async def fullSync(syncdata: schemas.FullSync, db: Session = Depends(getdb)):
    crud.fullSync(syncdata, db)
