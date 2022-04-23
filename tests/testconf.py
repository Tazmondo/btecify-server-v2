from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app, getdb
from app.models import Base, Song, Album, Artist, Playlist, PlaylistSong

DBNAME = "../db/test.db"

SQLALCHEMY_DATABASE_URL = "sqlite:///" + DBNAME

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def make_test_db():
    db: Session = TestingSessionLocal()
    with open(DBNAME, "w") as f:
        pass  # Overwrite db with no data to fully reset it

    # Make all tables
    Base.metadata.create_all(bind=engine)

    song1 = Song(
        title="song1",
        duration=50.3,
        extractor="youtube",
        disabled=True,
        data=b'some sound bytes',
        dataext='mp4',
        weburl="https://www.youtube.com/watch?v=iSqnJPdyqFM",
        thumbnail=b'some image bytes',
        thumbnailext='png',
        thumburl="https://i.ytimg.com/vi/iSqnJPdyqFM/hqdefault.jpg"
    )
    song2 = Song(
        title="song2",
        duration=22.3,
        extractor="bandcamp",
        disabled=False,
        data=b'some 2 sound bytes',
        dataext='mp4',
        weburl="https://www.youtube.com/watch?v=ggHN5ZJ8jkU",
        thumbnail=b'some 2 image bytes',
        thumbnailext='png',
        thumburl="https://i.ytimg.com/vi/ggHN5ZJ8jkU/hqdefault.jpg"
    )
    song3 = Song(
        title="song3",
        duration=10.3,
        extractor="youtube",
        disabled=False,
        data=b'some 3 sound bytes',
        dataext='mp4',
        weburl="https://www.youtube.com/watch?v=BbbcvFJ55F4",
        thumbnail=b'some 3 image bytes',
        thumbnailext='png',
        thumburl="https://i.ytimg.com/vi/BbbcvFJ55F4/hqdefault.jpg"
    )

    playlist1 = Playlist(
        title="playlist1",
        thumbnail=b'a playlist thumbnail',
    )
    playlist2 = Playlist(
        title="playlist2",
        thumbnail=b'a playlist thumbnail 2',
    )

    a1 = PlaylistSong(
        dateadded=datetime(2022, 4, 23, 2, 40),
        song=song1,
        playlist=playlist1
    )
    a2 = PlaylistSong(
        dateadded=datetime(2022, 4, 24, 2, 40),
        song=song2,
        playlist=playlist1
    )
    a3 = PlaylistSong(
        dateadded=datetime(2022, 4, 25, 2, 40),
        song=song2,
        playlist=playlist2
    )
    a4 = PlaylistSong(
        dateadded=datetime(2022, 4, 26, 2, 40),
        song=song3,
        playlist=playlist2
    )

    album1 = Album(
        title="album1",
        songs=[song2, song3]
    )
    album2 = Album(
        title="album2",
        songs=[song1]
    )

    artist1 = Artist(
        title="artist1",
        songs=album1.songs,
        albums=[album1]
    )
    artist2 = Artist(
        title="artist2",
        songs=album2.songs,
        albums=[album2]
    )

    db.add(playlist1)
    db.add(playlist2)
    db.commit()

    db.close()


def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[getdb] = get_test_db

client = TestClient(app)
