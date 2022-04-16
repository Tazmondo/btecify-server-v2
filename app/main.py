from fastapi import FastAPI, Depends, HTTPException, File
from sqlalchemy.orm import Session

import app.models as models
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
