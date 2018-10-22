from core.permissions import PermissionsEnum


class MessagePermissions(PermissionsEnum):
    VIEW = 'messages_view'
    VIEW_OTHERS = 'messages_view_others'
    VIEW_DELETED = 'messages_view_deleted'
    CREATE = 'messages_create'
    SEND = 'messages_send'
    MODIFY = 'messages_modify'
    MULTI_USER = 'messages_add_multiple_users'
    ADD_TO_OTHERS = 'messages_add_to_others'
