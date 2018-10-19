from typing import List

import flask
from voluptuous import Schema, Unordered

from core import APIException, db
from core.users.models import User
from core.utils import require_permission, validate_data
from messages.models import PMConversation, PMConversationState
from messages.permissions import PMPermissions

from . import bp

ALTER_MEMBERS_SCHEMA = Schema({
    'conv_id': int,
    'user_ids': Unordered([int]),
    })


@bp.route('/messages/conversations/members', methods=['POST'])
@require_permission(PMPermissions.MULTI_USER)
@validate_data(ALTER_MEMBERS_SCHEMA)
def add_members(conv_id: int, user_ids: List[int]):
    conv = PMConversation.from_pk(conv_id, _404=True, asrt=PMPermissions.VIEW_OTHERS)
    already_members = [u.username for u in conv.members if u.id in set(user_ids)]
    if already_members:
        raise APIException('The following members are already in the conversation: '
                           f'{", ".join(already_members)}.')
    for uid in list(set(user_ids)):
        PMConversationState.new(
            conv_id=conv_id,
            user_id=uid)
    conv.del_property_cache('members')
    return flask.jsonify(conv.members)


@bp.route('/messages/conversations/members', methods=['DELETE'])
@validate_data(ALTER_MEMBERS_SCHEMA)
def delete_members(conv_id: int, user_ids: List[int]):
    conv = PMConversation.from_pk(conv_id, _404=True, asrt=PMPermissions.VIEW_OTHERS)
    not_members = [uid for uid in user_ids if uid in {u.id for u in conv.members}]
    if not_members:
        raise APIException('The following members are not in the conversation: '  # type: ignore
                           f'{", ".join(not_members)}.')

    states = []
    og_members = []
    for uid in list(set(user_ids)):
        st = PMConversationState.from_attrs(conv_id=conv_id, user_id=uid)
        states.append(st)
        if st.original_member:
            og_members.append(User.from_pk(st.user_id).username)
    if og_members:
        raise APIException(
            'The following original members cannot be removed from the conversation: '
            f'{", ".join(og_members)}.')
    db.session.delete(states)
    db.session.commit()
    conv.del_property_cache('members')
    return flask.jsonify(conv.members)
