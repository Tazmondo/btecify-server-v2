import asyncio
from datetime import datetime

from sqlalchemy.orm import Session
from yt_dlp.utils import DownloadError

import app.models as models
import app.schemas as schemas
from app.extractor import downloadSong


def addSong(song: schemas.Song):
    data = downloadSong(song.weburl)


async def dbDownloadSong(db: Session, song: models.Song, force: bool = False):
    song = await fetchSong(song, force)

    db.commit()
    return song


async def dbDownloadPlaylist(db: Session, playlist: models.Playlist):
    songs = db.query(models.Song) \
        .join(models.Song.playlists) \
        .filter(models.PlaylistSong.playlist_id == playlist.id) \
        .all()

    results = await fetchSongs(songs)
    db.commit()
    return results


async def dbDownloadAll(db: Session):
    songs: list[models.Song] = db.query(models.Song).all()

    results = await fetchSongs(songs)
    db.commit()

    return results


async def fetchSongs(songs: list[models.Song]):
    # Fetch all songs concurrently
    results = await asyncio.gather(*[fetchSong(song) for song in songs], return_exceptions=True)
    failures = list(filter(lambda a: a not in results, songs))
    return failures


async def fetchSong(song: models.Song, force: bool = False):
    if ((song.data is None or song.dataext is None) and not song.disabled) or force:
        print(f"Fetching... {song.title} : {song.weburl}")
        try:
            songdownload = await downloadSong(song.weburl)

            song.data = songdownload.data
            song.dataext = songdownload.dataext

            song.thumburl = songdownload.info['thumbnail']
            song.thumbnail = songdownload.thumbdata
            song.thumbnailext = songdownload.thumbext

            song.disabled = False
        except DownloadError as e:
            if "video" in e.msg.lower():
                print(f"\n\nDISABLING {song.title}, COULD BE UNAVAILABLE.\n{e.msg}\n")
                song.disabled = True
            raise e
    return song


async def getSongSource(song: models.Song, db: Session):
    if song.disabled:
        raise ValueError(f"Disabled song was passed to getSongSource.", song)

    song = await dbDownloadSong(db, song)

    return song


async def getSongThumb(song: models.Song, db: Session):
    song = await dbDownloadSong(db, song, True)
    if song.thumbnail is not None:
        return song
    else:
        return False


def fullSync(syncdata: schemas.FullSync, db: Session):
    db.query(models.Song).delete()
    db.query(models.Album).delete()
    db.query(models.Artist).delete()
    db.query(models.Playlist).delete()
    db.query(models.PlaylistSong).delete()

    playlists = syncdata.playlists
    songsDict = {}
    artistDict = {}
    playlistDict = {}
    albumDict = {}


    # Initialise dicts with regular data instead of ORM.

    # for playlist in playlists:
    #
    #     # Initialise this playlist
    #     playlistDict[playlist.title] = {"title": playlist.title, "songs": []}
    #
    #     for song in playlist.songs:
    #
    #         # Add current song to the current playlist
    #         playlistDict[playlist.title]['songs'].append(song)
    #
    #         # Check for duplicate
    #         # If not duplicate, then need to initialise artist
    #         if song.weburl not in songsDict:
    #             songsDict[song.weburl] = song
    #
    #             if song.artist not in artistDict:
    #                 artistDict[song.artist] = {'name': song.artist, 'songs': [song], 'albums': []}
    #             else:
    #                 artistDict[song.artist]['songs'].append(song)
    #
    #             if song.album is not None:
    #                 if song.album not in albumDict:
    #                     albumDict[song.album] = {'title': song.album, 'songs': [song], 'artist': song.artist}
    #                     artistDict[song.artist]['albums'].append(albumDict[song.album])
    #                 else:
    #                     albumDict[song.album]['songs'].append(song)

    for playlist in playlists:

        # Initialise this playlist
        playlistDict[playlist.title] = models.Playlist(
            title=playlist.title
        )

        for song in playlist.songs:

            # Check for duplicate
            # If not duplicate, then need to initialise artist and album
            if song.weburl not in songsDict:

                # Make new song in db
                ormsong = models.Song(
                    title=song.title,
                    duration=song.duration,
                    extractor=song.extractor,
                    thumburl=song.thumburl,
                    weburl=song.weburl
                )

                songsDict[song.weburl] = ormsong

                if song.artist not in artistDict:
                    artistDict[song.artist] = models.Artist(
                        title=song.artist,
                        songs=[ormsong],
                        albums=[]
                    )
                else:
                    artistDict[song.artist].songs.append(ormsong)

                # Initialise album
                if song.album:
                    if song.album not in albumDict:
                        albumDict[song.album] = models.Album(
                            title=song.album,
                            artist=artistDict[song.artist],
                            songs=[ormsong]
                        )
                        artistDict[song.artist].albums.append(albumDict[song.album])
                    else:
                        albumDict[song.album].songs.append(ormsong)
            else:
                ormsong = songsDict[song.weburl]

            # Add current song to the current playlist
            # Must use association
            association = models.PlaylistSong(dateadded=datetime.now())
            association.song = ormsong
            association.playlist = playlistDict[playlist.title]

        db.add(playlistDict[playlist.title])

    db.commit()


if __name__ == "__main__":
    from app.db import SessionLocal

    db: Session = SessionLocal()

    fakeSong = models.Song(
        title="test1",
        duration=5,
        extractor="testextractor",
        weburl="bogusurl",

    )
    realSong = models.Song(
        title="testw",
        duration=5,
        extractor="youtube",
        weburl="youtube.com/watch?v=Y5KFnQYCdsk",

    )
    testPlaylist = models.Playlist(
        title="testplaylist"
    )
    models.PlaylistSong(
        dateadded=datetime.now(),
        song=fakeSong,
        playlist=testPlaylist
    )
    models.PlaylistSong(
        dateadded=datetime.now(),
        song=realSong,
        playlist=testPlaylist
    )
    # db.add(testPlaylist)

    testPlaylist = db.query(models.Playlist).first()
    # asyncio.run(downloadPlaylist(db, testPlaylist))

    # print(list(filter(lambda a: type(a) is not models.Song, asyncio.run(downloadAll(db)) )))
    print(asyncio.run(dbDownloadAll(db)))
    # asyncio.run(downloadPlaylist(db, db.query(models.Playlist).filter(models.Playlist.title=="music").first()))
