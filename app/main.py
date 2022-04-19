import io
from os import environ
from typing import Union

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from yt_dlp.utils import DownloadError

import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.db import SessionLocal

app = FastAPI()

if environ.get('devmode'):
    from fastapi_profiler.profiler_middleware import PyInstrumentProfilerMiddleware

    app.add_middleware(PyInstrumentProfilerMiddleware)


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


getSongResponses = {
    404:
        {
            "model": schemas.ExceptionResponse,
            "description": "Requested song couldn't be found."
        },
    410: {
        "model": schemas.ExceptionResponse,
        "description": "Song is disabled due to lack of a source"
    }
}


@app.get('/playlist', response_model=Union[list[schemas.ShallowPlaylist], list[schemas.Playlist]])
async def getPlaylists(shallow: bool = True, db=Depends(getdb)):
    playlistModels: list[models.Playlist] = db.query(models.Playlist).all()
    if shallow:
        response = [schemas.ShallowPlaylist.from_orm(x) for x in playlistModels]
    else:
        response = [schemas.Playlist.from_orm(x) for x in playlistModels]

    return response


@app.get('/playlist/{playlistid}', response_model=schemas.Playlist)
async def getPlaylist(playlistid: int, db: Session = Depends(getdb)):
    return db.query(models.Playlist).get(playlistid)


@app.put('/playlist/{playlistid}', response_model=schemas.Playlist)
async def putPlaylist(playlistid: int, newplaylist: schemas.PlaylistIn, db: Session = Depends(getdb)):
    playlistmodel: models.Playlist = db.query(models.Playlist).get(playlistid)

    if newplaylist.title is not None:
        playlistmodel.title = newplaylist.title

    if newplaylist.songs is not None:
        playlistmodel.songs = db.query(models.Song).filter(models.Song.id in newplaylist.songs).all()

    db.commit()
    return playlistmodel


@app.get('/song/{songid}', response_model=schemas.Song)
async def getSong(songid: int, db: Session = Depends(getdb)):
    return db.query(models.Song).get(songid)


@app.get('/song/{songid}/src', responses={
    200: {
        "content": {"audio/{requested data extension}": {}},
        "description": "Stream back the requested song",
    },
    469: {
        "model": schemas.ExceptionResponse,
        "description": "Could not download"
    },
    **getSongResponses
})
async def getSongSource(songid: int, db: Session = Depends(getdb)):
    dbsong = getSong(songid, db)
    if dbsong.disabled:
        raise HTTPException(status.HTTP_410_GONE, "Song is disabled due to lack of a source")

    if not dbsong.data:
        try:
            await crud.getSongSource(dbsong, db)
        except DownloadError as e:
            raise HTTPException(469, "Could not download", e)

    return StreamingResponse(io.BytesIO(dbsong.data), media_type=f"audio/{dbsong.dataext}")


@app.get('/song/{songid}/thumb', responses={
    200: {
        "content": {"image": {}},
        "description": "Stream back the requested thumbnail",
    },
    469: {
        "model": schemas.ExceptionResponse,
        "description": "Could not download"
    },
    **getSongResponses
})
async def getSongThumb(songid: int, db: Session = Depends(getdb)):
    dbsong = getSong(songid, db)
    if dbsong.disabled:
        raise HTTPException(status.HTTP_410_GONE, "Song is disabled due to lack of a source")

    if not dbsong.thumbnail:
        result = await crud.getSongThumb(dbsong, db)
        if not result:
            raise HTTPException(469, "Could not download")

    return StreamingResponse(io.BytesIO(dbsong.thumbnail), media_type=f"image/{dbsong.thumbnailext}")


@app.post('/song', response_model=schemas.Song)
async def postSong(song: schemas.SongIn, playlists: list[int], db: Session = Depends(getdb)):
    song = await crud.addSong(song, playlists, db)
    if not song:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Could not download song...")

    return song


@app.post('/fullsync')
async def fullSync(syncdata: schemas.FullSync, db: Session = Depends(getdb)):
    crud.fullSync(syncdata, db)


print("http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    print("main")
    testdb: Session = SessionLocal()
    testplaylist = testdb.query(models.Playlist).filter(models.Playlist.title == "eternal raijin").first()

    print(schemas.Playlist.from_orm(testplaylist))
