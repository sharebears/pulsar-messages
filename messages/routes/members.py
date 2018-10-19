from typing import List

import flask
from voluptuous import Schema

from core import APIException, db, cache
from core.users.models import User
from core.utils import require_permission, validate_data
from messages.models import PMConversation, PMConversationState
from messages.permissions import PMPermissions

from . import bp

ALTER_MEMBERS_SCHEMA = Schema({
    'user_ids': [int],
    })


@bp.route('/messages/<int:id>/members', methods=['POST'])
@require_permission(PMPermissions.MULTI_USER)
@validate_data(ALTER_MEMBERS_SCHEMA)
def add_members(id: int, user_ids: List[int]):
    conv = PMConversation.from_pk(id, _404=True, asrt=PMPermissions.VIEW_OTHERS)
    already_members = [u.username for u in conv.members if u.id in set(user_ids)]
    if already_members:
        raise APIException('The following members are already in the conversation: '
                           f'{", ".join(already_members)}.')
    for uid in list(set(user_ids)):
        PMConversationState.new(
            conv_id=id,
            user_id=uid)
    conv.del_property_cache('members')
    return flask.jsonify(conv.members)


@bp.route('/messages/<int:id>/members', methods=['DELETE'])
@validate_data(ALTER_MEMBERS_SCHEMA)
def delete_members(id: int, user_ids: List[int]):
    conv = PMConversation.from_pk(id, _404=True, asrt=PMPermissions.VIEW_OTHERS)
    not_members = [str(uid) for uid in user_ids if uid not in {u.id for u in conv.members}]
    if not_members:
        raise APIException('The following user_ids are not in the conversation: '  # type: ignore
                           f'{", ".join(not_members)}.')

    states = []
    og_members = []
    for uid in list(set(user_ids)):
        st = PMConversationState.from_attrs(conv_id=id, user_id=uid)
        states.append(st)
        if st.original_member:
            og_members.append(User.from_pk(st.user_id).username)
    if og_members:
        raise APIException(
            'The following original members cannot be removed from the conversation: '
            f'{", ".join(og_members)}.')
    for st in states:
        st.deleted = True
    db.session.commit()
    conv.del_property_cache('members')
    cache.delete(PMConversationState.__cache_key_members__.format(conv_id=conv.id))
    return flask.jsonify(conv.members)
