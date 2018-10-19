from typing import List

import flask
from voluptuous import All, In, Length, Range, Schema, Coerce

from core import _403Exception, db
from core.users.models import User
from core.utils import access_other_user, require_permission, validate_data
from messages.models import PMConversation, PMConversationState
from messages.permissions import PMPermissions

from . import bp

VIEW_CONVERSATIONS_SCHEMA = Schema({
    'page': All(Coerce(int), Range(min=0, max=2147483648)),
    'limit': All(Coerce(int), In((25, 50, 100))),
    'filter': All(str, In(('inbox', 'sentbox', 'deleted'))),
    })


@bp.route('/messages/conversations', methods=['GET'])
@require_permission(PMPermissions.VIEW)
@access_other_user(PMPermissions.VIEW_OTHERS)
@validate_data(VIEW_CONVERSATIONS_SCHEMA)
def view_conversations(user: User,
                       page: int = 1,
                       limit: int = 50,
                       filter: str = 'inbox'):
    return flask.jsonify({
        'conversations_count': PMConversation.count_from_user(user.id, filter=filter),
        'conversations': PMConversation.from_user(
            user_id=user.id,
            page=page,
            limit=limit,
            filter=filter),
        })


VIEW_CONVERSATION_SCHEMA = Schema({
    'page': All(Coerce(int), Range(min=0, max=2147483648)),
    'limit': All(Coerce(int), In((25, 50, 100))),
    })


@bp.route('/messages/conversations/<int:id>', methods=['GET'])
@require_permission(PMPermissions.VIEW)
@validate_data(VIEW_CONVERSATION_SCHEMA)
def view_conversation(id: int,
                      page: int = 1,
                      limit: int = 50):
    conv = PMConversation.from_pk(id, _404=True, asrt=PMPermissions.VIEW_OTHERS)
    conv.set_state(flask.g.user.id)
    conv.set_messages(page, limit)
    return flask.jsonify(conv)


CREATE_CONVERSATION_SCHEMA = Schema({
    'topic': All(str, Length(min=1, max=128)),
    'recipient_ids': [int],
    'message': str,
    })


@bp.route('/messages/conversations', methods=['POST'])
@require_permission(PMPermissions.CREATE)
@validate_data(CREATE_CONVERSATION_SCHEMA)
def create_conversation(topic: str,
                        recipient_ids: List[int],
                        message: str):
    if len(recipient_ids) > 1 and not flask.g.user.has_permission(PMPermissions.MULTI_USER):
        raise _403Exception('You cannot create a conversation with multiple users.')
    pm = PMConversation.new(
        topic=topic,
        sender_id=flask.g.user.id,
        recipient_ids=recipient_ids,
        initial_message=message)
    pm.set_state(flask.g.user.id)
    return flask.jsonify(pm)


@bp.route('/messages/conversations/<int:id>', methods=['DELETE'])
@require_permission(PMPermissions.DELETE)
@access_other_user(PMPermissions.VIEW_OTHERS)
def delete_conversation(user: User, id: int):
    pm_state = PMConversationState.from_attrs(
        conv_id=id,
        user_id=user.id,
        deleted='f')
    if not pm_state:
        raise _403Exception('You cannot delete a conversation that you are not a member of.')
    pm_state.deleted = True
    db.session.commit()
    PMConversation.clear_cache_keys(user.id)
    return flask.jsonify(f'Successfully deleted conversation {id}.')
