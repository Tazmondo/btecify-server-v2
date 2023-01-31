import asyncio
import io
from datetime import datetime
from os import environ
from typing import Union

from fastapi import FastAPI, Depends, HTTPException, status, Response, WebSocket, WebSocketDisconnect, Header
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from yt_dlp.utils import DownloadError

import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.db import SessionLocal, engine
from app.extractor import get_data
from app.jobmanager import jobs, get_job, delete_job
from app.models import Base

app = FastAPI()
Base.metadata.create_all(bind=engine)

if environ.get('devmode'):
    pass

    # app.add_middleware(PyInstrumentProfilerMiddleware)


# Dependency
def getdb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def getSongFromDb(songid: int, db: Session):
    dbsong: models.Song = db.query(models.Song).get(songid)
    if not dbsong:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Song not found")
    return dbsong


getSongResponses = {
    404: {
        "model": schemas.ExceptionResponse,
        "description": "Requested song couldn't be found."
    },
    410: {
        "model": schemas.ExceptionResponse,
        "description": "Song is disabled due to lack of a source"
    },
}


@app.get('/ping')
async def pong():
    return {'ping': 'pong'}


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
    playlist = db.query(models.Playlist).get(playlistid)
    if playlist is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Requested playlist does not exist.")
    return playlist


@app.put('/playlist/{playlistid}', response_model=schemas.Playlist)
async def putPlaylist(playlistid: int, newplaylist: schemas.PlaylistIn, db: Session = Depends(getdb)):
    playlistmodel: models.Playlist = db.query(models.Playlist).get(playlistid)
    if playlistmodel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Requested playlist does not exist.")

    if playlistmodel.title is not None:
        playlistmodel.title = newplaylist.title

    if newplaylist.songs is not None:
        try:
            crud.addSongsToPlaylist(playlistmodel.id, newplaylist.songs, db, clear=True)
        except ValueError:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Requested songs not found.")

    db.commit()
    return playlistmodel


@app.post('/playlist', response_model=schemas.Playlist)
async def postPlaylist(playlist: schemas.PlaylistIn, db: Session = Depends(getdb)):
    if db.query(models.Playlist).filter_by(title=playlist.title).first() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Playlist with title {playlist.title} already exists.")

    if playlist.songs is None:
        playlist.songs = []

    found_songs = db.query(models.Song).filter(models.Song.id.in_(playlist.songs)).all()

    newPlaylist = models.Playlist(
        title=playlist.title,
    )

    newPlaylist.songs = [models.PlaylistSong(
        song=song,
        playlist=newPlaylist,
        dateadded=datetime.now()
    ) for song in found_songs]

    db.add(newPlaylist)
    db.commit()
    return newPlaylist


@app.delete('/playlist/{playlist_id}')
async def deletePlaylist(playlist_id: int, db: Session = Depends(getdb)):
    playlist = db.get(models.Playlist, playlist_id)
    if playlist is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Could not find provided playlist")

    db.delete(playlist)
    db.commit()
    return "Deletion successful"


@app.get('/song', response_model=list[schemas.Song])
async def getSongs(db: Session = Depends(getdb)):
    return db.query(models.Song).all()


@app.get('/song/{songid}', response_model=schemas.Song)
async def getSong(songid: int, db: Session = Depends(getdb)):
    song = db.query(models.Song).get(songid)
    if song is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Requested song does not exist.")

    return song


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
async def getSongSource(songid: int,
                        request_range: str | None = Header(default=None, alias="Range"),
                        db: Session = Depends(getdb)):
    dbsong = getSongFromDb(songid, db)
    if dbsong.disabled:
        raise HTTPException(status.HTTP_410_GONE, "Song is disabled due to lack of a source")

    if not dbsong.data_uuid:
        try:
            await crud.getSongSource(dbsong, db)
        except DownloadError as e:
            raise HTTPException(469, "Could not download")

    song_data = get_data(dbsong.data_uuid, dbsong.dataext)

    data_length = len(song_data)

    # OLD COMMENT, REFERENCES CONTENTS OF FIRST BRANCH OF IF STATEMENT
    # So that the audio player can seek to given times
    # If 206 is not returned then (on chromium at least), audio player cannot seek
    # Content length is the total length of the content
    # Content range (i assume) is the range of bytes of this response, used by the player
    #   to construct audio from chunks, but here we just send it all at once.
    #       it might be better to send it chunked but i cba to write that code rn

    print(request_range)

    if request_range is None or not request_range.startswith("bytes="):
        return StreamingResponse(io.BytesIO(song_data), media_type=f"audio/{dbsong.dataext}", status_code=206, headers={
            "Accept-Ranges": 'bytes',
            "Content-Length": str(data_length),
            "Content-Range": f"bytes 0-{str(data_length)}/{str(data_length)}"
        })
    else:
        start_byte = int(request_range[6:-1])
        song_data = song_data[start_byte:]
        return StreamingResponse(io.BytesIO(song_data), media_type=f"audio/{dbsong.dataext}", status_code=206, headers={
            "Accept-Ranges": 'bytes',
            "Content-Length": str(data_length),
            "Content-Range": f"bytes {str(start_byte)}-{str(data_length)}/{str(data_length)}"
        })


@app.get('/song/{songid}/thumb', response_model=str)
async def getSongThumb(songid: int, db: Session = Depends(getdb)):
    dbsong = getSongFromDb(songid, db)
    if not dbsong:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not a valid song")

    if not dbsong.thumbnail:
        result = await crud.getSongThumb(dbsong, db)
        if not result:
            raise HTTPException(469, "Could not download")
    thumbnail: models.Thumbnail = dbsong.thumbnail
    ext = thumbnail.ext
    if ext.startswith('.'):  # Because some extensions in db might start with .
        ext = ext[1:]
        thumbnail.ext = ext
        db.commit()

    # Don't do ranges, could have been the cause of the weird half image loading issue that btecifyv3 had?
    return str(thumbnail.id)


@app.get('/thumb/{thumbid}')
async def getThumb(thumbid: int, db: Session = Depends(getdb)):
    thumb = db.get(models.Thumbnail, thumbid)
    if thumb is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Thumbnail not found")

    ext = thumb.ext
    data = get_data(thumb.data_uuid, thumb.ext)

    return StreamingResponse(io.BytesIO(data), media_type=f"image/{ext}", headers={
        "cache-control": "public, max-age=31536000"  # Cache for one year
    })


@app.post('/song', response_model=schemas.Song)
async def postSong(song: schemas.SongIn, playlists: list[int], response: Response, db: Session = Depends(getdb)):
    oldSong = db.query(models.Song).filter(models.Song.weburl == song.weburl).first()
    if oldSong is not None:
        for playlist_id in playlists:
            crud.addSongsToPlaylist(playlist_id, [oldSong.id], db)

        response.status_code = status.HTTP_204_NO_CONTENT
        return oldSong

    song = await crud.addSong(song, playlists, db)
    if not song:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Could not download song")

    return song


@app.post('/fullsync')
async def fullSync(syncdata: schemas.FullSync, db: Session = Depends(getdb)):
    crud.fullSync(syncdata, db)


@app.post('/fulldownload', response_model=str)
async def fullDownload():
    db: Session = SessionLocal()

    def finished():
        db.close()

    try:
        allSongs = db.query(models.Song).filter(
            and_(or_(models.Song.data_uuid == None, models.Song.dataext == None), models.Song.disabled == False)).all()
        job_id = await crud.downloadExistingSongsJob(allSongs, db, finished)
        return job_id
    except Exception as e:
        finished()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, e)


@app.websocket('/job/{job_id}')
async def job_websocket(websocket: WebSocket, job_id: str):
    job = get_job(job_id)
    if job is None:
        await websocket.close(3006)
        return

    await websocket.accept()
    try:
        while True:
            client_data = await websocket.receive_text()
            await websocket.send_json(
                schemas.Job(**job.__dict__).dict())  # Make new schema with just important info from just
            if job.status:
                # Close websocket when job completion is sent.
                await websocket.close(code=3005)
                raise WebSocketDisconnect
            await asyncio.sleep(0.5)  # Max update rate is 0.5 no matter how fast client requests the data.
    except WebSocketDisconnect:
        # delete_job(job_id)  # Mark job for deletion
        pass


@app.on_event('startup')
async def clearJobTask():
    async def task():
        while True:
            await asyncio.sleep(30)
            currentTime = datetime.now()
            for job in list(
                    jobs.values()):  # Use list because cannot delete from an iterator while iterating through it
                time_diff = (currentTime - job.last_used).total_seconds()
                if (time_diff > 30 and job.status is True) or time_diff > 180:  # Soft and hard timeouts of 10 and 60.
                    if time_diff > 180:
                        print("\nWARNING: JOB HARD TIMED OUT.")
                        print(job, end='\n\n')

                    delete_job(job.job_id)

    asyncio.create_task(task())


print("http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    print("main")
    testdb: Session = SessionLocal()
    testplaylist = testdb.query(models.Playlist).filter(models.Playlist.title == "eternal raijin").first()

    print(schemas.Playlist.from_orm(testplaylist))
