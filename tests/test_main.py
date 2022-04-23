from testconf import client


def test_pong():
    response = client.get('/ping')
    assert response.status_code == 200
    data = response.json()
    assert data == {'ping': 'pong'}
