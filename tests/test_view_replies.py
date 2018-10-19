import json
from core import db


def test_create_reply(app, authed_client):
    response = authed_client.post('/messages/replies', data=json.dumps({
        'conv_id': 1,
        'message': 'new message',
        })).get_json()['response']
    assert response['contents'] == 'new message'
    assert response['conv_id'] == 1


def test_create_reply_noperms(app, authed_client):
    db.engine.execute('DELETE FROM users_permissions')
    response = authed_client.post('/messages/replies', data=json.dumps({
        'conv_id': 1,
        'message': 'new message',
        })).get_json()['response']
    assert response == 'You do not have permission to access this resource.'
