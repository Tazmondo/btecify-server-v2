from datetime import datetime

from sqlalchemy.orm import Session

import app.schemas as schemas
import app.models as models
from app.extractor import downloadSong


def addSong(song: schemas.Song):
    data = downloadSong(song.weburl)


def downloadAll(db: Session):
    songs: list[models.Song] = db.query(models.Song).all()

    for song in songs:

        songdownload = downloadSong(song.weburl)
        song.data = songdownload.data
        song.dataext = songdownload.dataext

        song.thumburl = songdownload.info['thumbnail']
        song.thumbnail = songdownload.thumbdata
        song.thumbnailext = songdownload.thumbext


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
    from main import SessionLocal
    db: Session = SessionLocal()

    db.commit()
