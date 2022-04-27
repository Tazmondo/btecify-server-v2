from testconf import client, make_test_db


def test_pong():
    make_test_db()
    response = client.get('/ping')
    assert response.status_code == 200
    data = response.json()
    assert data == {'ping': 'pong'}


def test_get_playlists():
    make_test_db()
    response = client.get('/playlist')
    assert response.status_code == 200
    data = response.json()
    assert repr(data) == ("[{'id': 1, 'title': 'playlist1', 'songs': [1, 3, 2]}, {'id': 2, 'title': "
                          "'playlist2', 'songs': [4, 3]}]")

    response = client.get('/playlist', params={'shallow': "False"})
    assert response.status_code == 200
    data = response.json()
    assert repr(
        data) == (
               "[{'id': 1, 'title': 'playlist1', 'songs': [{'id': 1, 'title': 'song1', ""'album': {'id': 1, 'title': 'album2'}, 'duration': 50.3, 'extractor': ""'youtube', 'weburl': 'https://www.youtube.com/watch?v=iSqnJPdyqFM', ""'artist': {'id': 1, 'title': 'artist2'}, 'dateadded': '2022-04-23T02:40:00', ""'playlists': [{'id': 1, 'title': 'playlist1', 'dateadded': ""'2022-04-23T02:40:00'}]}, {'id': 3, 'title': 'song2', 'album': {'id': 2, ""'title': 'album1'}, 'duration': 22.3, 'extractor': 'bandcamp', 'weburl': ""'https://www.youtube.com/watch?v=ggHN5ZJ8jkU', 'artist': {'id': 2, 'title': ""'artist1'}, 'dateadded': '2022-04-24T02:40:00', 'playlists': [{'id': 1, ""'title': 'playlist1', 'dateadded': '2022-04-24T02:40:00'}, {'id': 2, ""'title': 'playlist2', 'dateadded': '2022-04-25T02:40:00'}]}, {'id': 2, ""'title': 'song4', 'album': {'id': 1, 'title': 'album2'}, 'duration': None, ""'extractor': None, 'weburl': 'a bad url', 'artist': {'id': 1, 'title': ""'artist2'}, 'dateadded': '2022-04-26T02:40:00', 'playlists': [{'id': 1, ""'title': 'playlist1', 'dateadded': '2022-04-26T02:40:00'}]}]}, {'id': 2, ""'title': 'playlist2', 'songs': [{'id': 4, 'title': 'song3', 'album': {'id': ""2, 'title': 'album1'}, 'duration': 10.3, 'extractor': 'youtube', 'weburl': ""'https://www.youtube.com/watch?v=BbbcvFJ55F4', 'artist': {'id': 2, 'title': ""'artist1'}, 'dateadded': '2022-04-26T02:40:00', 'playlists': [{'id': 2, ""'title': 'playlist2', 'dateadded': '2022-04-26T02:40:00'}]}, {'id': 3, ""'title': 'song2', 'album': {'id': 2, 'title': 'album1'}, 'duration': 22.3, ""'extractor': 'bandcamp', 'weburl': ""'https://www.youtube.com/watch?v=ggHN5ZJ8jkU', 'artist': {'id': 2, 'title': ""'artist1'}, 'dateadded': '2022-04-25T02:40:00', 'playlists': [{'id': 1, ""'title': 'playlist1', 'dateadded': '2022-04-24T02:40:00'}, {'id': 2, ""'title': 'playlist2', 'dateadded': '2022-04-25T02:40:00'}]}]}]")

    response = client.get('/playlist', params={'shallow': '100'})
    assert response.status_code == 422


def test_get_playlist():
    make_test_db()
    response = client.get('/playlist/1')
    assert response.status_code == 200
    assert repr(
        response.json()) == (
               "{'id': 1, 'title': 'playlist1', 'songs': [{'id': 1, 'title': 'song1', ""'album': {'id': 1, 'title': 'album2'}, 'duration': 50.3, 'extractor': ""'youtube', 'weburl': 'https://www.youtube.com/watch?v=iSqnJPdyqFM', ""'artist': {'id': 1, 'title': 'artist2'}, 'dateadded': '2022-04-23T02:40:00', ""'playlists': [{'id': 1, 'title': 'playlist1', 'dateadded': ""'2022-04-23T02:40:00'}]}, {'id': 3, 'title': 'song2', 'album': {'id': 2, ""'title': 'album1'}, 'duration': 22.3, 'extractor': 'bandcamp', 'weburl': ""'https://www.youtube.com/watch?v=ggHN5ZJ8jkU', 'artist': {'id': 2, 'title': ""'artist1'}, 'dateadded': '2022-04-24T02:40:00', 'playlists': [{'id': 1, ""'title': 'playlist1', 'dateadded': '2022-04-24T02:40:00'}, {'id': 2, ""'title': 'playlist2', 'dateadded': '2022-04-25T02:40:00'}]}, {'id': 2, ""'title': 'song4', 'album': {'id': 1, 'title': 'album2'}, 'duration': None, ""'extractor': None, 'weburl': 'a bad url', 'artist': {'id': 1, 'title': ""'artist2'}, 'dateadded': '2022-04-26T02:40:00', 'playlists': [{'id': 1, ""'title': 'playlist1', 'dateadded': '2022-04-26T02:40:00'}]}]}")

    response = client.get('/playlist/10000')
    assert response.status_code == 404
    assert response.json() == {'detail': 'Requested playlist does not exist.'}
    print("")


def test_put_playlist():
    make_test_db()
    response = client.put('/playlist/1')
    assert response.status_code == 422

    response = client.put('/playlist/10000', json={'title': 'a valid title'})
    assert response.status_code == 404

    response = client.put('/playlist/1', json={'title': 'valid', 'songs': [1, 2, 3, 4, 5, 43, 5, 43]})
    assert response.status_code == 404

    # Individual title
    updateTitle = {'title': 'updated title'}

    response = client.put('/playlist/1', json=updateTitle)
    data = response.json()

    assert response.status_code == 200
    assert data['title'] == "updated title"

    # Both together
    make_test_db()
    updateTitle = {'title': 'updated title', 'songs': [2, 3]}

    response = client.put('/playlist/1', json=updateTitle)
    data = response.json()

    assert response.status_code == 200
    assert data['title'] == "updated title"

    # Basically just check if all the songs provided in updatetitle were actually added to the returned playlist
    # assert all(map(lambda songid: songid in map(lambda playlistsong: playlistsong['id'], data['songs']), updateTitle['songs']))
    assert all(map(lambda playlistsong: playlistsong['id'] in updateTitle['songs'], data['songs']))


def test_post_playlist():
    make_test_db()
    newplaylist = {'title': "new test playlist", "songs": [2]}
    response = client.post('/playlist', json=newplaylist)
    assert response.status_code == 200
    data = response.json()
    assert data['title'] == newplaylist['title']
    assert all(map(lambda playlistsong: playlistsong['id'] in newplaylist['songs'], data['songs']))

    response = client.post('/playlist', json=newplaylist)
    assert response.status_code == 409

    make_test_db()
    newplaylist = {'title': "new test playlist", "songs": []}
    response = client.post('/playlist', json=newplaylist)
    assert response.status_code == 200
    data = response.json()
    assert data == {'title': 'new test playlist', 'songs': [], 'id': 3}


def test_get_song():
    make_test_db()
    response = client.get('/song/1')
    assert (response.status_code == 200)
    assert (repr(
        response.json()) == "{'id': 1, 'title': 'song1', 'album': {'id': 1, 'title': 'album2'}, 'duration': 50.3, 'extractor': 'youtube', 'weburl': 'https://www.youtube.com/watch?v=iSqnJPdyqFM', 'artist': {'id': 1, 'title': 'artist2'}, 'playlists': [{'id': 1, 'title': 'playlist1', 'dateadded': '2022-04-23T02:40:00'}]}")

    response = client.get('/song/21893712132')
    assert (response.status_code == 404)
    assert (response.json()['detail'] == "Requested song does not exist.")

    response = client.get('/song/-1')
    assert (response.status_code == 404)
    assert (response.json()['detail'] == "Requested song does not exist.")


def test_get_song_src():
    make_test_db()
    response = client.get('/song/3/src')
    assert (response.status_code == 200)
    assert (response.content == b'some 2 sound bytes')

    response = client.get('/song/1/src')
    assert (response.status_code == 410)

    response = client.get('/song/2/src')
    assert (response.status_code == 469)


def test_get_song_thumb():
    make_test_db()
    response = client.get('/song/3/thumb')
    assert (response.status_code == 200)
    assert (response.content == b'some image bytes')
    assert (response.headers['content-type'] == 'image/png')

    response = client.get('/song/1/src')
    assert (response.status_code == 410)

    response = client.get('/song/2/src')
    assert (response.status_code == 469)


def test_post_song():
    make_test_db()
    # Goals for this test:
    #   add a new song !
    #   test that get song endpoint returns right song !
    #   test that the source endpoint returns the right source !
    #   test that given playlists do contain the song !
    #   test that given artist and album contain the song ?

    #   test that duplicate song weburls cause 204 and add to other playlists. !
    #   test song with invalid url !
    #   test song with playlists that dont exist !
    #   test song with an artist/album that doesnt exist yet

    newsong = {
        'song': {
            'weburl': "https://www.youtube.com/watch?v=ntX9LYIc5Ak",
            'title': "the new song",
            'artist': "artist1",
            'album': 'album1'
        },
        'playlists': [1]
    }
    response = client.post('/song', json=newsong)
    data = response.json()
    assert (response.status_code == 200)
    assert (data['title'] == newsong['song']['title'])
    assert (data['album']['title'] == newsong['song']['album'])
    assert (data['artist']['title'] == newsong['song']['artist'])
    assert (len(data['playlists']) == len(newsong['playlists']))

    id = data['id']
    response_song_get = client.get('/song/' + str(id))
    data2 = response_song_get.json()

    assert (data == data2)

    musichex = "0000001C6674797069736F6D0000020069736F6D69736F326D7034310000"
    response_source = client.get('/song/' + str(id) + '/src')
    assert (response_source.content.hex().upper()[:60] == musichex)

    thumbhex = "524946464EA20000574542505650382042A200003054049D012A0005D002"
    response_thumb = client.get('/song/' + str(id) + '/thumb')
    assert (response_thumb.content.hex().upper()[:60] == thumbhex)

    response_playlist = map(lambda song: song['id'], client.get('/playlist/1').json()['songs'])

    assert (id in response_playlist)

    newsong = {
        'song': {
            'weburl': "https://www.youtube.com/watch?v=ntX9LYIc5Ak",
            'title': "the new song",
            'artist': "artist1",
            'album': 'album1'
        },
        'playlists': [1, 2]
    }
    response = client.post('/song', json=newsong)
    data = response.json()
    id = data['id']
    assert (response.status_code == 204)
    response_playlist1 = map(lambda song: song['id'], client.get('/playlist/1').json()['songs'])
    response_playlist2 = map(lambda song: song['id'], client.get('/playlist/2').json()['songs'])

    assert (id in response_playlist1 and id in response_playlist2)

    make_test_db()

    newsong = {
        'song': {
            'weburl': "hehehehaha",
            'title': "the new song",
            'artist': "artist1",
            'album': 'album1'
        },
        'playlists': [1, 2]
    }
    playlists = client.get('/playlist', params={'shallow': False}).json()
    response = client.post('/song', json=newsong)
    playlists2 = client.get('/playlist', params={'shallow': False}).json()
    assert (response.status_code == 500)
    assert (playlists == playlists2)  # Make sure no changes are committed.

    make_test_db()

    newsong = {
        'song': {
            'weburl': "https://www.youtube.com/watch?v=ntX9LYIc5Ak",
            'title': "the new song",
            'artist': "artist1",
            'album': 'album1'
        },
        'playlists': [1, 2, 12312312]
    }
    response = client.post('/song', json=newsong)
    assert (response.status_code == 200)
