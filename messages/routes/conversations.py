from typing import List

import flask
from voluptuous import All, Coerce, In, Length, Range, Schema

from core import _403Exception, db
from core.users.models import User
from core.utils import access_other_user, require_permission, validate_data
from messages.models import PrivateConversation, PrivateConversationState
from messages.permissions import MessagePermissions

from . import bp

VIEW_CONVERSATIONS_SCHEMA = Schema(
    {
        'page': All(Coerce(int), Range(min=0, max=2147483648)),
        'limit': All(Coerce(int), In((25, 50, 100))),
        'filter': All(str, In(('inbox', 'sentbox', 'deleted'))),
    }
)


@bp.route('/messages/conversations', methods=['GET'])
@require_permission(MessagePermissions.VIEW)
@access_other_user(MessagePermissions.VIEW_OTHERS)
@validate_data(VIEW_CONVERSATIONS_SCHEMA)
def view_conversations(
    user: User, page: int = 1, limit: int = 50, filter: str = 'inbox'
):
    return flask.jsonify(
        {
            'conversations_count': PrivateConversation.count_from_user(
                user.id, filter=filter
            ),
            'conversations': PrivateConversation.from_user(
                user_id=user.id, page=page, limit=limit, filter=filter
            ),
        }
    )


VIEW_CONVERSATION_SCHEMA = Schema(
    {
        'page': All(Coerce(int), Range(min=0, max=2147483648)),
        'limit': All(Coerce(int), In((25, 50, 100))),
    }
)


@bp.route('/messages/conversations/<int:id>', methods=['GET'])
@require_permission(MessagePermissions.VIEW)
@validate_data(VIEW_CONVERSATION_SCHEMA)
def view_conversation(id: int, page: int = 1, limit: int = 50):
    conv = PrivateConversation.from_pk(
        id, _404=True, asrt=MessagePermissions.VIEW_OTHERS
    )
    conv.set_state(flask.g.user.id)
    conv.set_messages(page, limit)
    if page * limit > conv.messages_count:
        conv.mark_read()
    return flask.jsonify(conv)


CREATE_CONVERSATION_SCHEMA = Schema(
    {
        'topic': All(str, Length(min=1, max=128)),
        'recipient_ids': [int],
        'message': str,
    }
)


@bp.route('/messages/conversations', methods=['POST'])
@require_permission(MessagePermissions.CREATE)
@validate_data(CREATE_CONVERSATION_SCHEMA)
def create_conversation(topic: str, recipient_ids: List[int], message: str):
    if len(recipient_ids) > 1 and not flask.g.user.has_permission(
        MessagePermissions.MULTI_USER
    ):
        raise _403Exception(
            'You cannot create a conversation with multiple users.'
        )
    pm = PrivateConversation.new(
        topic=topic,
        sender_id=flask.g.user.id,
        recipient_ids=recipient_ids,
        initial_message=message,
    )
    pm.set_state(flask.g.user.id)
    return flask.jsonify(pm)


MODIFY_CONVERSATIONS_SCHEMA = Schema(
    {'conversation_ids': [int], 'read': bool, 'deleted': bool}
)


@bp.route('/messages/conversations', methods=['PUT'])
@require_permission(MessagePermissions.MODIFY)
@access_other_user(MessagePermissions.VIEW_OTHERS)
@validate_data(MODIFY_CONVERSATIONS_SCHEMA)
def modify_conversations(
    user: User,
    conversation_ids: List[int],
    read: bool = None,
    deleted: bool = None,
):
    conversations = []
    failed: List[str] = []
    for conv_id in conversation_ids:
        pm_state = PrivateConversationState.from_attrs(
            conv_id=conv_id, user_id=user.id, deleted='f'
        )
        if not pm_state:
            failed.append(str(conv_id))
        else:
            conversations.append(pm_state)
    if failed:
        raise _403Exception(
            f'You cannot modify conversations that you are not a member of: {", ".join(failed)}.'
        )
    for conv in conversations:
        if read:
            conv.read = read
        if deleted:
            conv.deleted = deleted
    db.session.commit()
    PrivateConversation.clear_cache_keys(user.id)
    return flask.jsonify(
        f'Successfully modified conversations {", ".join(str(c.conv_id) for c in conversations)}.'
    )


MODIFY_CONVERSATION_SCHEMA = Schema({'read': bool, 'deleted': bool})


@bp.route('/messages/conversations/<int:id>', methods=['PUT'])
@require_permission(MessagePermissions.MODIFY)
@access_other_user(MessagePermissions.VIEW_OTHERS)
@validate_data(MODIFY_CONVERSATION_SCHEMA)
def modify_conversation(
    user: User, id: int, read: bool = None, deleted: bool = None
):
    pm_state = PrivateConversationState.from_attrs(
        conv_id=id, user_id=user.id, deleted='f'
    )
    if not pm_state:
        raise _403Exception(
            'You cannot modify a conversation that you are not a member of.'
        )
    if read:
        pm_state.read = read
    if deleted:
        pm_state.deleted = deleted
    db.session.commit()
    PrivateConversation.clear_cache_keys(user.id)
    return flask.jsonify(f'Successfully modified conversation {id}.')
