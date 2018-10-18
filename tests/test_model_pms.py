import pytest
from conftest import check_dictionary, add_permissions
from core import NewJSONEncoder
from messages.models import PMConversation, PMMessage
from messages.exceptions import PMStateNotFound
from messages.permissions import PMPermissions


def test_get_conversation(client):
    pm = PMConversation.from_pk(1)
    assert pm.id == 1
    assert pm.topic == 'New Private Message!'
    assert len(pm.members) == 2
    assert all(m.id in {1, 2} for m in pm.members)


def test_get_conversation_multiple_members(client):
    pm = PMConversation.from_pk(2)
    assert len(pm.members) == 3
    assert all(m.id in {1, 2, 3} for m in pm.members)
    assert len(pm.messages) == 2


def test_create_new_conversation_and_messages_from_conversation(client):
    pm = PMConversation.new(
        topic='test1',
        sender_id=3,
        recipient_ids=[2],
        initial_message='testing')
    assert pm.topic == 'test1'
    assert pm.id == 5
    pm_messages = PMMessage.from_conversation(5)
    assert len(pm_messages) == 1
    assert pm_messages[0].contents == 'testing'
    assert pm_messages[0].user_id == 3


def test_conversation_set_state(client):
    pm = PMConversation.from_pk(2)
    pm.set_state(2)
    assert pm.read is False
    assert pm.sticky is False
    pm.set_state(1)
    assert pm.read is True
    assert pm.sticky is True


def test_conversation_set_state_nonexistent(client):
    pm = PMConversation.from_pk(1)
    with pytest.raises(PMStateNotFound):
        pm.set_state(3)


def test_belongs_to_user(authed_client):
    assert PMConversation.from_pk(1).belongs_to_user()
    assert PMConversation.from_pk(2).belongs_to_user()


def test_not_belongs_to_user(authed_client):
    assert not PMConversation.from_pk(4).belongs_to_user()


def test_set_messages_limit(client):
    pm = PMConversation.from_pk(2)
    pm.set_messages(page=1, limit=1)
    assert len(pm.messages) == 1
    assert pm.messages[0].id == 2


def test_set_messages_pagination(client):
    pm = PMConversation.from_pk(2)
    pm.set_messages(page=2, limit=1)
    assert len(pm.messages) == 1
    assert pm.messages[0].id == 6


def test_serialize_basic_perms(authed_client):
    pm = PMConversation.from_pk(1)
    pm.set_state(1)
    data = NewJSONEncoder().default(pm)
    check_dictionary(data, {
        'id': 1,
        'topic': 'New Private Message!',
        })


def test_serialize_view_fail(authed_client):
    pm = PMConversation.from_pk(4)
    data = NewJSONEncoder().default(pm)
    assert data is None


def test_serialize_view_others(app, authed_client):
    add_permissions(app, PMPermissions.VIEW_OTHERS)
    pm = PMConversation.from_pk(4)
    pm.set_state(2)
    data = NewJSONEncoder().default(pm)
    check_dictionary(data, {
        'id': 4,
        'topic': 'detingstings',
        })
