import flask
from voluptuous import Schema

from core.utils import require_permission, validate_data
from messages.models import PMConversation, PMMessage
from messages.permissions import PMPermissions

from . import bp

CREATE_REPLY_SCHEMA = Schema({
    'conv_id': int,
    'message': str,
    })


@bp.route('/messages/replies', methods=['POST'])
@require_permission(PMPermissions.SEND)
@validate_data(CREATE_REPLY_SCHEMA)
def create_reply(conv_id: int, message: str):
    conv = PMConversation.from_pk(conv_id, _404=True)
    return flask.jsonify(PMMessage.new(
        conv_id=conv.id,
        user_id=flask.g.user.id,
        contents=message))
