from testconf import client, make_test_db


def test_pong():
    make_test_db()
    response = client.get('/ping')
    assert response.status_code == 200
    data = response.json()
    assert data == {'ping': 'pong'}


def test_get_playlists_shallow():
    make_test_db()
    response = client.get('/playlist')
    assert response.status_code == 200
    data = response.json()
    assert repr(
        data) == "[{'id': 1, 'title': 'playlist1', 'songs': [1, 2]}, {'id': 2, 'title': 'playlist2', 'songs': [3, 2]}]"


def test_get_playlists_deep():
    make_test_db()
    response = client.get('/playlist', params={'shallow': "False"})
    assert response.status_code == 200
    data = response.json()
    assert repr(
        data) == "[{'id': 1, 'title': 'playlist1', 'songs': [{'id': 1, 'title': 'song1', 'album': {'id': 1, 'title': 'album2'}, 'duration': 50.3, 'extractor': 'youtube', 'weburl': 'https://www.youtube.com/watch?v=iSqnJPdyqFM', 'artist': {'id': 1, 'title': 'artist2'}, 'dateadded': '2022-04-23T02:40:00', 'playlists': [{'id': 1, 'title': 'playlist1', 'dateadded': '2022-04-23T02:40:00'}]}, {'id': 2, 'title': 'song2', 'album': {'id': 2, 'title': 'album1'}, 'duration': 22.3, 'extractor': 'bandcamp', 'weburl': 'https://www.youtube.com/watch?v=ggHN5ZJ8jkU', 'artist': {'id': 2, 'title': 'artist1'}, 'dateadded': '2022-04-24T02:40:00', 'playlists': [{'id': 1, 'title': 'playlist1', 'dateadded': '2022-04-24T02:40:00'}, {'id': 2, 'title': 'playlist2', 'dateadded': '2022-04-25T02:40:00'}]}]}, {'id': 2, 'title': 'playlist2', 'songs': [{'id': 3, 'title': 'song3', 'album': {'id': 2, 'title': 'album1'}, 'duration': 10.3, 'extractor': 'youtube', 'weburl': 'https://www.youtube.com/watch?v=BbbcvFJ55F4', 'artist': {'id': 2, 'title': 'artist1'}, 'dateadded': '2022-04-26T02:40:00', 'playlists': [{'id': 2, 'title': 'playlist2', 'dateadded': '2022-04-26T02:40:00'}]}, {'id': 2, 'title': 'song2', 'album': {'id': 2, 'title': 'album1'}, 'duration': 22.3, 'extractor': 'bandcamp', 'weburl': 'https://www.youtube.com/watch?v=ggHN5ZJ8jkU', 'artist': {'id': 2, 'title': 'artist1'}, 'dateadded': '2022-04-25T02:40:00', 'playlists': [{'id': 1, 'title': 'playlist1', 'dateadded': '2022-04-24T02:40:00'}, {'id': 2, 'title': 'playlist2', 'dateadded': '2022-04-25T02:40:00'}]}]}]"
