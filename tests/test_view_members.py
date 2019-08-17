import json

import pytest

from conftest import add_permissions
from core import db
from messages.permissions import MessagePermissions


def test_add_members_to_conversation(app, authed_client):
    add_permissions(app, MessagePermissions.MULTI_USER)
    response = authed_client.post(
        '/messages/1/members', data=json.dumps({'user_ids': [4, 5]})
    ).get_json()['response']
    assert len(response) == 5
    assert all(u['id'] in {1, 2, 3, 4, 5} for u in response)


def test_add_members_to_conversation_already_in(app, authed_client):
    add_permissions(app, MessagePermissions.MULTI_USER)
    response = authed_client.post(
        '/messages/1/members', data=json.dumps({'user_ids': [2, 4]})
    ).get_json()['response']
    assert (
        response
        == 'The following members are already in the conversation: user_two.'
    )


def test_add_members_to_others_conversation(app, authed_client):
    add_permissions(
        app, MessagePermissions.MULTI_USER, MessagePermissions.VIEW_OTHERS
    )
    response = authed_client.post(
        '/messages/4/members', data=json.dumps({'user_ids': [1]})
    ).get_json()['response']
    assert len(response) == 3
    assert any(u['id'] == 1 for u in response)


def test_attempt_add_members_to_others_conversation(app, authed_client):
    add_permissions(app, MessagePermissions.MULTI_USER)
    response = authed_client.post(
        '/messages/4/members', data=json.dumps({'user_ids': [1]})
    ).get_json()['response']
    assert response == 'PrivateConversation 4 does not exist.'


def test_delete_members_from_conversation(app, authed_client):
    add_permissions(app, MessagePermissions.MULTI_USER)
    response = authed_client.delete(
        '/messages/1/members', data=json.dumps({'user_ids': [3]})
    ).get_json()['response']
    assert len(response) == 2
    assert all(u['id'] in {1, 2} for u in response)


def test_delete_original_members_from_conversation(app, authed_client):
    add_permissions(app, MessagePermissions.MULTI_USER)
    response = authed_client.delete(
        '/messages/3/members', data=json.dumps({'user_ids': [2]})
    ).get_json()['response']
    assert (
        response
        == 'The following original members cannot be removed from the conversation: user_two.'
    )


def test_delete_nonexistent_members_from_conversation(app, authed_client):
    add_permissions(app, MessagePermissions.MULTI_USER)
    response = authed_client.delete(
        '/messages/3/members', data=json.dumps({'user_ids': [5]})
    ).get_json()['response']
    assert response == 'The following user_ids are not in the conversation: 5.'


@pytest.mark.parametrize('endpoint, method', [('/messages/1/members', 'POST')])
def test_route_permissions(app, authed_client, endpoint, method):
    db.engine.execute('DELETE FROM users_permissions')
    response = authed_client.open(endpoint, method=method).get_json()[
        'response'
    ]
    assert response == 'You do not have permission to access this resource.'
