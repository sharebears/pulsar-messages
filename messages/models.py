from datetime import datetime
from typing import List, Optional

import flask
from sqlalchemy import and_, exists, func, select
from sqlalchemy.ext.hybrid import hybrid_property

from core import _403Exception, cache, db
from core.mixins import MultiPKMixin, SinglePKMixin
from core.users.models import User
from core.utils import cached_property
from messages.exceptions import PMStateNotFound
from messages.permissions import PMPermissions
from messages.serializers import PMConversationSerializer, PMMessageSerializer


class PMConversation(db.Model, SinglePKMixin):
    __tablename__ = 'pm_conversations'
    __cache_key__ = 'pm_conversations_{id}'
    __cache_key_of_user__ = 'pm_conversations_users_{user_id}_{filter}'
    __cache_key_msg_count__ = 'pm_conversations_{id}_messages_count'
    __cache_key_conv_count__ = 'pm_conversations_{id}_conversations_count_{filter}'
    __serializer__ = PMConversationSerializer

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(128), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    locked = db.Column(db.Boolean, nullable=False, server_default='f')

    @classmethod
    def from_user(cls,
                  user_id: int,
                  page: int = 1,
                  limit: int = 50,
                  filter: str = 'inbox') -> List['PMConversation']:
        conversations = cls.get_many(
            key=cls.__cache_key_of_user__.format(user_id=user_id, filter=filter),
            filter=cls.id.in_(db.session.query(
                PMConversationState.conv_id
                ).filter(cls.get_pm_state_filters(user_id, filter))),
            page=page,
            limit=limit)
        for conv in conversations:
            conv.set_state(user_id)
        return conversations

    @classmethod
    def count_from_user(cls,
                        user_id: int,
                        filter: str = 'inbox') -> int:
        return PMConversationState.count(
            key=cls.__cache_key_conv_count__.format(id=user_id, filter=filter),
            attribute=PMConversationState.conv_id,
            filter=cls.get_pm_state_filters(user_id, filter))

    @staticmethod
    def get_pm_state_filters(user_id, filter):
        if filter == 'deleted' and not flask.g.user.has_permission(PMPermissions.VIEW_DELETED):
            raise _403Exception
        filters = [PMConversationState.user_id == user_id,
                   PMConversationState.deleted == ('f' if filter != 'deleted' else 't')]
        if filter == 'inbox':
            filters.append(PMConversationState.last_response_time.isnot(None))
        elif filter == 'sentbox':
            filters.append(PMConversationState.in_sentbox.is_(True))
        return and_(*filters)

    @classmethod
    def new(cls,
            topic: str,
            sender_id: int,
            recipient_ids: List[int],
            initial_message: str,
            locked: bool = False) -> Optional['PMConversation']:
        """
        Create a private message object, set states for the sender and receiver,
        and create the initial message.
        """
        User.is_valid(sender_id, error=True)
        for rid in recipient_ids:
            User.is_valid(rid, error=True)

        pm_conversation = super()._new(
            topic=topic,
            sender_id=sender_id,
            locked=locked)

        PMConversationState.new(
            conv_id=pm_conversation.id,
            user_id=sender_id,
            original_member=True,
            read=True)
        for user_id in recipient_ids:
            PMConversationState.new(
                conv_id=pm_conversation.id,
                user_id=user_id,
                original_member=True)

        PMMessage.new(
            conv_id=pm_conversation.id,
            user_id=sender_id,
            contents=initial_message)
        return pm_conversation

    @classmethod
    def clear_cache_keys(cls, user_id: int):
        cache.delete_many(*(
            cls.__cache_key_of_user__.format(user_id=user_id, filter=f)
            for f in ['inbox', 'sentbox', 'deleted']))

    @property
    def messages(self):
        if not hasattr(self, '_messages'):
            self._messages = PMMessage.from_conversation(self.id)
        return self._messages

    @cached_property
    def members(self):
        return PMConversationState.get_users_in_conversation(self.id)

    @cached_property
    def messages_count(self):
        return PMMessage.count(
            key=self.__cache_key_msg_count__.format(id=self.id),
            attribute=PMMessage.id,
            filter=PMMessage.conv_id == self.id)

    def set_state(self, user_id):
        """
        Assign the state of the PM for a user to attributes of this object. This makes
        the object suitable for serialization.
        """
        self._conv_state = PMConversationState.from_attrs(conv_id=self.id, user_id=user_id)
        if not self._conv_state:
            raise PMStateNotFound
        self.read = self._conv_state.read
        self.sticky = self._conv_state.sticky
        self.last_response_time = self._conv_state.last_response_time

    def set_messages(self,
                     page: int = 1,
                     limit: int = 50) -> None:
        self._messages = PMMessage.from_conversation(self.id, page, limit)

    def belongs_to_user(self) -> bool:
        """
        Override of base class method to check against all users with a conversation state.
        """
        return flask.g.user is not None and flask.g.user.id in {u.id for u in self.members}


class PMConversationState(db.Model, MultiPKMixin):
    __tablename__ = 'pm_conversations_state'
    __cache_key__ = 'pm_convesations_state_{conv_id}_{user_id}'
    __cache_key_members__ = 'pm_conversations_state_{conv_id}_members'

    conv_id = db.Column(db.Integer, db.ForeignKey('pm_conversations.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    original_member = db.Column(db.Boolean, nullable=False)
    read = db.Column(db.Boolean, nullable=False, server_default='f')
    sticky = db.Column(db.Boolean, nullable=False, server_default='f', index=True)
    deleted = db.Column(db.Boolean, nullable=False, server_default='f', index=True)
    time_added = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    last_response_time = db.Column(db.DateTime(timezone=True))

    @hybrid_property
    def in_sentbox(cls):
        return select([exists().where(and_(
            PMMessage.conv_id == cls.conv_id,
            PMMessage.user_id == cls.user_id,
            cls.deleted == 'f',
            ))]).as_scalar()

    @classmethod
    def get_users_in_conversation(cls, conv_id: int) -> List[User]:
        return User.get_many(pks=cls.get_user_ids_in_conversation(conv_id))

    @classmethod
    def get_user_ids_in_conversation(cls, conv_id: int) -> List[int]:
        return cls.get_col_from_many(
            column=cls.user_id,
            key=cls.__cache_key_members__.format(conv_id=conv_id),
            filter=and_(cls.conv_id == conv_id, cls.deleted == 'f'),
            order=cls.time_added.asc())

    @classmethod
    def new(cls,
            conv_id: int,
            user_id: int,
            original_member: bool = False,
            read: bool = False) -> Optional['PMConversationState']:
        """
        Create a private message object, set states for the sender and receiver,
        and create the initial message.
        """
        PMConversation.is_valid(conv_id, error=True)
        User.is_valid(user_id, error=True)
        cache.delete(cls.__cache_key_members__.format(conv_id=conv_id))
        return super()._new(
            conv_id=conv_id,
            user_id=user_id,
            original_member=original_member,
            read=read)

    @classmethod
    def update_last_response_time(cls,
                                  conv_id: int,
                                  sender_id: int) -> None:
        db.session.query(cls).filter(and_(
            cls.conv_id == conv_id,
            cls.user_id != sender_id,
            )).update({'last_response_time': datetime.utcnow()})
        db.session.commit()
        cache.delete_many(*(cls.create_cache_key({
            'conv_id': conv_id, 'user_id': uid
            }) for uid in cls.get_user_ids_in_conversation(conv_id) if uid != sender_id))


class PMMessage(db.Model, SinglePKMixin):
    __tablename__ = 'pm_messages'
    __cache_key__ = 'pm_messages_{id}'
    __cache_key_of_conversation__ = 'pm_messages_conv_{conv_id}'
    __serializer__ = PMMessageSerializer

    id = db.Column(db.Integer, primary_key=True)
    conv_id = db.Column(
        db.Integer, db.ForeignKey('pm_conversations.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    time = db.Column(
        db.DateTime(timezone=True), nullable=False, index=True, server_default=func.now())
    contents = db.Column(db.Text, nullable=False)

    @classmethod
    def from_conversation(cls,
                          conv_id: int,
                          page: int = 1,
                          limit: int = 50) -> List['PMMessage']:
        """
        Get a list of private messages in a conversation.
        """
        return cls.get_many(
            key=cls.__cache_key_of_conversation__.format(conv_id=conv_id),
            filter=cls.conv_id == conv_id,
            order=cls.time.asc(),
            page=page,
            limit=limit)

    @classmethod
    def new(cls,
            conv_id: int,
            user_id: int,
            contents: str) -> Optional['PMMessage']:
        """
        Create a message in a PM conversation.
        """
        PMConversation.is_valid(conv_id, error=True)
        User.is_valid(user_id, error=True)
        PMConversationState.update_last_response_time(conv_id, user_id)
        return super()._new(
            conv_id=conv_id,
            user_id=user_id,
            contents=contents)
