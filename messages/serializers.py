from core.mixins import Attribute, Serializer
from messages.permissions import PMPermissions


class PMConversationSerializer(Serializer):
    id = Attribute(permission=PMPermissions.VIEW_OTHERS)
    topic = Attribute(permission=PMPermissions.VIEW_OTHERS)
    last_updated_time = Attribute(permission=PMPermissions.VIEW_OTHERS)
    messages = Attribute(nested=False, permission=PMPermissions.VIEW_OTHERS)
    members = Attribute(nested=('id', 'name'), permission=PMPermissions.VIEW_OTHERS)


class PMMessageSerializer(Serializer):
    # These are essentially permissioned in the conversation, since messages
    # are never rendered outside of a conversation. No need to run the checks
    # again.
    id = Attribute()
    conv_id = Attribute()
    user_id = Attribute()
    time = Attribute()
    contents = Attribute()
