from fastapi import FastAPI, Depends, HTTPException, File
from sqlalchemy.orm import Session

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


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get('/api/songsource')
async def getSongSource(songId: int, db: Session = Depends(getdb)):
    dbSong: models.Song = db.query(models.Song).get(songId)
    if not dbSong:
        raise HTTPException(404, "Song not found")


@app.post('/api/song')
async def addSong(song: schemas.SongIn):
    pass


@app.post('/api/fullsync')
async def fullSync():
    pass


# todo: get artists, then merge on client transfer to server, eliminate similar names and merge into 1
