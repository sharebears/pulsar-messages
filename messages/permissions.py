from core.permissions import PermissionsEnum


class PMPermissions(PermissionsEnum):
    VIEW = 'messages_view'
    VIEW_OTHERS = 'messages_view_others'
    CREATE = 'messages_create'
    SEND = 'messages_send'
    DELETE = 'messages_delete'
    MULTI_USER = 'messages_add_multiple_users'
