import asyncio
from datetime import datetime
from hashlib import md5
from typing import Union, Callable

from sqlalchemy.orm import Session
from yt_dlp.utils import DownloadError

import app.models as models
import app.schemas as schemas
from app.extractor import downloadSong
from app.jobmanager import start_job


async def addSong(song: schemas.SongIn, playlists: list[int], db: Session) -> Union[models.Song, bool]:
    playlistModels = db.query(models.Playlist).filter(models.Playlist.id.in_(playlists)).all()

    try:
        songDownload: schemas.SongDownload = await downloadSong(song.weburl)
    except DownloadError:
        return False

    if songDownload.data is None:
        return False

    meta = songDownload.info

    artist = song.artist or meta.get('artist') or meta.get('uploader') or None
    album = song.album or meta.get('album') or None

    artistModel = db \
        .query(models.Artist) \
        .filter(models.Artist.title == artist) \
        .first()

    if artist and not artistModel:
        artistModel = models.Artist(
            title=artist
        )

    albumModel = db \
        .query(models.Album) \
        .filter(models.Album.title == album) \
        .first()

    if album and not albumModel:
        albumModel = models.Album(
            title=album
        )

    thumbhash = md5(songDownload.thumbdata).hexdigest()
    thumbobj = db.query(models.Thumbnail).filter(models.Thumbnail.hash == thumbhash).first()
    if thumbobj is None:
        thumbobj = models.Thumbnail(
            hash=thumbhash,
            data=songDownload.thumbdata,
            ext=songDownload.thumbext
        )

    playlist_additions = [models.PlaylistSong(
        dateadded=datetime.now(),
        playlist=playlist
    ) for playlist in playlistModels]

    try:
        songModel = models.Song(
            weburl=meta.get('webpage_url') or song.weburl,
            title=song.title or meta.get('track') or meta['title'],
            duration=meta['duration'],
            artist=artistModel or None,
            album=albumModel or None,
            playlists=playlist_additions,
            extractor=meta.get('extractor_key'),
            data=songDownload.data,
            dataext=songDownload.dataext,
            thumbnail=thumbobj,
        )
    except KeyError as e:
        print(e)
        return False

    db.add(songModel)
    db.commit()

    return songModel


async def dbDownloadSong(db: Session, song: models.Song, force: bool = False):
    song = await downloadExistingSong(song, db, force)

    db.commit()
    return song


async def dbDownloadPlaylist(db: Session, playlist: models.Playlist):
    songs = db.query(models.Song) \
        .join(models.Song.playlists) \
        .filter(models.PlaylistSong.playlist_id == playlist.id) \
        .all()

    results = await downloadExistingSongs(songs, db)
    db.commit()
    return results


async def dbDownloadAll(db: Session):
    songs: list[models.Song] = db.query(models.Song).all()

    results = await downloadExistingSongs(songs, db)
    db.commit()

    return results


async def downloadExistingSongsJob(songs: list[models.Song], db: Session, finish_func: Callable = None):
    # Fetch all songs concurrently
    download_coroutines = [downloadExistingSong(song, db) for song in songs]

    async def finished():
        print("Finished fulldownload, comitting to db...")
        db.commit()
        if finish_func is not None:
            finish_func()

    job_id = await start_job(download_coroutines, finished())
    return job_id


async def downloadExistingSongs(songs: list[models.Song], db: Session):
    # Fetch all songs concurrently
    results = await asyncio.gather(*[downloadExistingSong(song, db) for song in songs], return_exceptions=True)
    failures = list(filter(lambda a: a not in results, songs))
    return failures


async def downloadExistingSong(song: models.Song, db: Session, force: bool = False):
    if ((song.data is None or song.dataext is None) and not song.disabled) or force:
        print(f"Fetching... {song.title} : {song.weburl}")
        try:
            songdownload = await downloadSong(song.weburl)

            song.data = songdownload.data
            song.dataext = songdownload.dataext
            song.extractor = songdownload.extractor
            song.duration = songdownload.info['duration']

            song.thumburl = songdownload.info['thumbnail']

            thumbhash = md5(songdownload.thumbdata).hexdigest()
            thumbobj = db.query(models.Thumbnail).filter(models.Thumbnail.hash == thumbhash).first()
            if thumbobj:
                song.thumbnail = thumbobj
            else:
                song.thumbnail = models.Thumbnail(
                    hash=thumbhash,
                    data=songdownload.thumbdata,
                    ext=songdownload.thumbext
                )

            song.disabled = False
            print(f"Fetched {song.title} : {song.weburl}, {song.dataext}")
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
    try:
        song = await dbDownloadSong(db, song, True)
        if song.thumbnail is not None:
            return song
        else:
            return False
    except DownloadError as e:
        return False


def addSongsToPlaylist(playlist_id: int, song_ids: list[int], db: Session, clear: bool = False):
    playlist = db.get(models.Playlist, playlist_id)
    if playlist is None:
        return False

    newsongs = db.query(models.Song).filter(models.Song.id.in_(song_ids)).all()

    if len(newsongs) != len(song_ids):  # All inputted songs should be valid.
        raise ValueError(f"{len(song_ids) - len(newsongs)} inputted songs were invalid.")

    oldsongs = []
    if not clear:
        oldsongs = playlist.songs
        newsongs = list(
            filter(lambda song: song.id not in map(lambda playlistsong: playlistsong.song_id, playlist.songs),
                   newsongs))

    playlist.songs = oldsongs + [
        models.PlaylistSong(
            playlist=playlist,
            song=song,
            dateadded=datetime.now()
        ) for song in newsongs
    ]

    db.commit()
    return True


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
                    weburl=song.weburl,
                    duration=song.duration or None,
                    extractor=song.extractor or None,
                )

                songsDict[song.weburl] = ormsong

                if song.artist:
                    if song.artist not in artistDict:
                        artistDict[song.artist] = models.Artist(
                            title=song.artist,
                            songs=[ormsong],
                        )
                    else:
                        artistDict[song.artist].songs.append(ormsong)

                # Initialise album
                if song.album:
                    if song.album not in albumDict:
                        albumDict[song.album] = models.Album(
                            title=song.album,
                            songs=[ormsong]
                        )
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

    db1: Session = SessionLocal()

    songs1: list[models.Song] = db1.query(models.Album).filter(
        models.Album.title == "Minecraft - Volume Alpha").first().songs1

    [print(md5(x.thumbnail).digest()) for x in songs1]


    def func1():
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
