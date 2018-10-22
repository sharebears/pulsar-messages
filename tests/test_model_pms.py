from datetime import datetime

import pytest
import pytz

from conftest import add_permissions, check_dictionary
from core import NewJSONEncoder, _403Exception, cache
from messages.exceptions import PMStateNotFound
from messages.models import PrivateConversation, PrivateMessage, PrivateConversationState
from messages.permissions import MessagePermissions


def test_get_conversation(client):
    pm = PrivateConversation.from_pk(1)
    assert pm.id == 1
    assert pm.topic == 'New Private Message!'
    assert len(pm.members) == 3
    assert all(m.id in {1, 2, 3} for m in pm.members)


def test_get_conversation_multiple_members(client):
    pm = PrivateConversation.from_pk(2)
    assert len(pm.members) == 3
    assert all(m.id in {1, 2, 3} for m in pm.members)
    assert len(pm.messages) == 2


def test_create_new_conversation_and_messages_from_conversation(client):
    pm = PrivateConversation.new(
        topic='test1',
        sender_id=3,
        recipient_ids=[2],
        initial_message='testing')
    assert pm.topic == 'test1'
    assert pm.id == 5
    pm_messages = PrivateMessage.from_conversation(5)
    assert len(pm_messages) == 1
    assert pm_messages[0].contents == 'testing'
    assert pm_messages[0].user_id == 3


def test_make_message(client):
    pm = PrivateConversation.from_pk(1)
    pm.set_state(1)
    pm_state = PrivateConversationState.from_attrs(conv_id=1, user_id=1)
    assert (datetime.utcnow().replace(tzinfo=pytz.utc) - pm.last_response_time
            ).total_seconds() > 60 * 60
    assert cache.has(pm_state.cache_key)
    PrivateMessage.new(conv_id=1, user_id=2, contents='hi')
    assert not cache.has(pm_state.cache_key)
    pm.set_state(1)
    assert (datetime.utcnow().replace(tzinfo=pytz.utc) - pm.last_response_time
            ).total_seconds() < 15


def test_conversation_from_user_inbox(client):
    convs = PrivateConversation.from_user(1)
    assert len(convs) == 2
    assert all(c.id in {1, 2} for c in convs)


def test_conversation_from_user_sentbox(client):
    convs = PrivateConversation.from_user(1, filter='sentbox')
    assert len(convs) == 3
    assert all(c.id in {1, 2, 3} for c in convs)


def test_conversation_from_user_deletebox(app, authed_client):
    add_permissions(app, MessagePermissions.VIEW_DELETED)
    convs = PrivateConversation.from_user(3, filter='deleted')
    assert len(convs) == 1
    assert convs[0].id == 3


def test_conversation_from_user_deletebox_empty(app, authed_client):
    add_permissions(app, MessagePermissions.VIEW_DELETED)
    convs = PrivateConversation.from_user(1, filter='deleted')
    assert len(convs) == 0


def test_conversation_from_user_deletebox_no_perm(authed_client):
    with pytest.raises(_403Exception):
        PrivateConversation.from_user(1, filter='deleted')


def test_conversation_set_state(client):
    pm = PrivateConversation.from_pk(2)
    pm.set_state(2)
    assert pm.read is False
    assert pm.sticky is False
    pm.set_state(1)
    assert pm.read is True
    assert pm.sticky is True


def test_conversation_set_state_nonexistent(client):
    pm = PrivateConversation.from_pk(1)
    with pytest.raises(PMStateNotFound):
        pm.set_state(5)


def test_belongs_to_user(authed_client):
    assert PrivateConversation.from_pk(1).belongs_to_user()
    assert PrivateConversation.from_pk(2).belongs_to_user()


def test_not_belongs_to_user(authed_client):
    assert not PrivateConversation.from_pk(4).belongs_to_user()


def test_set_messages_limit(client):
    pm = PrivateConversation.from_pk(2)
    pm.set_messages(page=1, limit=1)
    assert len(pm.messages) == 1
    assert pm.messages[0].id == 3


def test_set_messages_pagination(client):
    pm = PrivateConversation.from_pk(2)
    pm.set_messages(page=2, limit=1)
    assert len(pm.messages) == 1
    assert pm.messages[0].id == 4


def test_clear_cache_keys(client):
    for uid in [1, 2]:
        for f in ['inbox', 'sentbox', 'deleted']:
            cache.set(PrivateConversation.__cache_key_of_user__.format(user_id=uid, filter=f), 1)
    PrivateConversation.clear_cache_keys(1)
    for f in ['inbox', 'sentbox', 'deleted']:
        assert not cache.has(PrivateConversation.__cache_key_of_user__.format(user_id=1, filter=f))
        assert cache.has(PrivateConversation.__cache_key_of_user__.format(user_id=2, filter=f))


def test_serialize_basic_perms(authed_client):
    pm = PrivateConversation.from_pk(1)
    pm.set_state(1)
    data = NewJSONEncoder().default(pm)
    check_dictionary(data, {
        'id': 1,
        'topic': 'New Private Message!',
        })


def test_serialize_view_fail(authed_client):
    pm = PrivateConversation.from_pk(4)
    data = NewJSONEncoder().default(pm)
    assert data is None


def test_serialize_view_others(app, authed_client):
    add_permissions(app, MessagePermissions.VIEW_OTHERS)
    pm = PrivateConversation.from_pk(4)
    pm.set_state(2)
    data = NewJSONEncoder().default(pm)
    check_dictionary(data, {
        'id': 4,
        'topic': 'detingstings',
        })
