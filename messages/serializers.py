from core.mixins import Attribute, Serializer
from messages.permissions import PMPermissions


class PMConversationSerializer(Serializer):
    id = Attribute(permission=PMPermissions.VIEW_OTHERS)
    topic = Attribute(permission=PMPermissions.VIEW_OTHERS)
    last_response_time = Attribute(permission=PMPermissions.VIEW_OTHERS)
    read = Attribute(permission=PMPermissions.VIEW_OTHERS)
    sticky = Attribute(permission=PMPermissions.VIEW_OTHERS)
    messages = Attribute(nested=False, permission=PMPermissions.VIEW_OTHERS)
    messages_count = Attribute(permission=PMPermissions.VIEW_OTHERS)
    members = Attribute(permission=PMPermissions.VIEW_OTHERS)


class PMMessageSerializer(Serializer):
    # These are essentially permissioned in the conversation, since messages
    # are never rendered outside of a conversation. No need to run the checks
    # again.
    id = Attribute()
    conv_id = Attribute()
    user = Attribute(nested=('id', 'username'))
    time = Attribute()
    contents = Attribute()
