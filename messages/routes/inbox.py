import flask
from . import bp
from core.users.models import User
from voluptuous import All, In, Range, Schema
from core.utils import access_other_user, require_permission, validate_data
from messages.permissions import PMPermissions

app = flask.current_app


VIEW_INBOX_SCHEMA = Schema({
    'page': All(int, Range(min=0, max=2147483648)),
    'limit': All(int, In((25, 50, 100))),
    'filter': All(str, In(('inbox', 'sentbox', 'deleted'))),
    })


@bp.route('/messages', methods=['GET'])
@require_permission(PMPermissions.VIEW)
@access_other_user(PMPermissions.VIEW_OTHERS)
@validate_data(VIEW_INBOX_SCHEMA)
def view_inbox(user: User,
               page: int = 1,
               limit: int = 50,
               filter: str = 'inbox') -> flask.Response:
    pass
