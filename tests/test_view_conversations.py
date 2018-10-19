from messages.permissions import PMPermissions
import pytest
import json
from messages.models import PMConversation, PMConversationState
from core import db
from conftest import add_permissions


def test_view_conversations(app, authed_client):
    response = authed_client.get('/messages/conversations').get_json()
    response = response['response']
    assert len(response['conversations']) == 2
    assert all(c['id'] in {1, 2} for c in response['conversations'])


def test_view_conversations_paginated_page(app, authed_client):
    response = authed_client.get('/messages/conversations', query_string={'page': 2}).get_json()
    response = response['response']
    assert len(response['conversations']) == 0
    assert response['conversations_count'] == 2


def test_view_sentbox(app, authed_client):
    response = authed_client.get(
        '/messages/conversations', query_string={'filter': 'sentbox'}).get_json()
    response = response['response']
    assert len(response['conversations']) == 3
    assert all(c['id'] in {1, 2, 3} for c in response['conversations'])


def test_view_conversations_others(app, authed_client):
    add_permissions(app, PMPermissions.VIEW_OTHERS)
    response = authed_client.get('/messages/conversations', query_string={'user_id': 2}).get_json()
    response = response['response']
    assert len(response['conversations']) == 3
    assert all(c['id'] in {1, 2, 3} for c in response['conversations'])


def test_view_conversations_others_perm_fail(app, authed_client):
    response = authed_client.get('/messages/conversations', query_string={'user_id': 2})
    assert response.status_code == 403


def test_view_conversation(app, authed_client):
    response = authed_client.get('/messages/conversations/1')
    json = response.get_json()['response']
    assert len(json['messages']) == 2
    assert json['read'] is True


def test_view_conversation_pagination(app, authed_client):
    response = authed_client.get('/messages/conversations/1', query_string={'page': 2})
    json = response.get_json()['response']
    assert len(json['messages']) == 0
    assert json['messages_count'] == 2
    assert json['read'] is True


def test_view_conversation_deleted(app, authed_client):
    PMConversationState.from_attrs(conv_id=1, user_id=1).deleted = True
    db.session.commit()
    response = authed_client.get('/messages/conversations/1').get_json()['response']
    assert response == 'PMConversation 1 does not exist.'


def test_create_conversation(app, authed_client):
    response = authed_client.post('/messages/conversations', data=json.dumps({
        'topic': 'New test topic',
        'recipient_ids': [2],
        'message': 'testing for you',
        })).get_json()['response']
    assert len(response['messages']) == 1
    assert response['topic'] == 'New test topic'
    assert len(response['members']) == 2
    assert all(m['id'] in {1, 2} for m in response['members'])
    assert response['read'] is True


def test_create_conversation_bad_recipient_ids(app, authed_client):
    response = authed_client.post('/messages/conversations', data=json.dumps({
        'topic': 'New test topic',
        'recipient_ids': ['ab'],
        'message': 'testing for you',
        })).get_json()['response']
    assert response == 'Invalid data: expected int (key "recipient_ids.0")'


def test_create_conversation_multi_user(app, authed_client):
    add_permissions(app, PMPermissions.MULTI_USER)
    response = authed_client.post('/messages/conversations', data=json.dumps({
        'topic': 'New test topic',
        'recipient_ids': [2, 3],
        'message': 'testing for you',
        })).get_json()['response']
    assert len(response['messages']) == 1
    assert response['topic'] == 'New test topic'
    assert len(response['members']) == 3
    assert all(m['id'] in {1, 2, 3} for m in response['members'])


def test_create_conversation_multi_user_no_perm(app, authed_client):
    response = authed_client.post('/messages/conversations', data=json.dumps({
        'topic': 'New test topic',
        'recipient_ids': [2, 3],
        'message': 'testing for you',
        })).get_json()['response']
    assert response == 'You cannot create a conversation with multiple users.'


def test_delete_conversation(app, authed_client):
    add_permissions(app, PMPermissions.VIEW_DELETED)
    response = authed_client.delete('/messages/conversations/1').get_json()['response']
    assert response == 'Successfully deleted conversation 1.'

    convs = PMConversation.from_user(1, filter='deleted')
    assert len(convs) == 1
    assert convs[0].id == 1
    convs = PMConversation.from_user(1, filter='inbox')
    assert len(convs) == 1


def test_delete_already_deleted_conversation(app, authed_client):
    PMConversationState.from_attrs(conv_id=1, user_id=1).deleted = True
    db.session.commit()
    response = authed_client.delete('/messages/conversations/1').get_json()['response']
    assert response == 'You cannot delete a conversation that you are not a member of.'


def test_delete_conversation_not_member_of(app, authed_client):
    response = authed_client.delete('/messages/conversations/4').get_json()['response']
    assert response == 'You cannot delete a conversation that you are not a member of.'


def test_delete_conversation_permission_override(app, authed_client):
    add_permissions(app, PMPermissions.VIEW_OTHERS)
    response = authed_client.delete(
        '/messages/conversations/4', query_string={'user_id': 2}).get_json()['response']
    assert response == 'Successfully deleted conversation 4.'
    assert PMConversationState.from_attrs(conv_id=4, user_id=2).deleted is True


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/messages/conversations', 'GET'),
        ('/messages/conversations/1', 'GET'),
        ('/messages/conversations', 'POST'),
        ('/messages/conversations/1', 'DELETE'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    db.engine.execute('DELETE FROM users_permissions')
    response = authed_client.open(endpoint, method=method).get_json()['response']
    assert response == 'You do not have permission to access this resource.'
