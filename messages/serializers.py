from core.mixins import Attribute, Serializer
from messages.permissions import MessagePermissions


class PrivateConversationSerializer(Serializer):
    id = Attribute(permission=MessagePermissions.VIEW_OTHERS)
    topic = Attribute(permission=MessagePermissions.VIEW_OTHERS)
    last_response_time = Attribute(permission=MessagePermissions.VIEW_OTHERS)
    read = Attribute(permission=MessagePermissions.VIEW_OTHERS)
    sticky = Attribute(permission=MessagePermissions.VIEW_OTHERS)
    messages = Attribute(
        nested=False, permission=MessagePermissions.VIEW_OTHERS
    )
    messages_count = Attribute(permission=MessagePermissions.VIEW_OTHERS)
    members = Attribute(permission=MessagePermissions.VIEW_OTHERS)


class PrivateMessageSerializer(Serializer):
    # These are essentially permissioned in the conversation, since messages
    # are never rendered outside of a conversation. No need to run the checks
    # again.
    id = Attribute()
    conv_id = Attribute()
    user = Attribute(nested=('id', 'username'))
    time = Attribute()
    contents = Attribute()
