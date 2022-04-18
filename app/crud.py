from sqlalchemy.orm import Session

from app import schemas
from app import models
from app.extractor import downloadSong


def addSong(song: schemas.Song):
    data = downloadSong(song.weburl)



if __name__ == "__main__":
    from main import SessionLocal
    db: Session = SessionLocal()

    db.commit()
