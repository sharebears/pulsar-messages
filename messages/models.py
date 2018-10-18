from typing import List, Optional

import flask
from sqlalchemy import and_, exists, func, select
from sqlalchemy.ext.hybrid import hybrid_property

from core import db
from core.mixins import MultiPKMixin, SinglePKMixin
from core.users.models import User
from messages.exceptions import PMStateNotFound
from messages.serializers import PMConversationSerializer, PMMessageSerializer


class PMConversation(db.Model, SinglePKMixin):
    __tablename__ = 'pm_conversations'
    __cache_key__ = 'pm_conversation_{id}'
    __serializer__ = PMConversationSerializer

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(128), nullable=False)
    last_updated_time = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    @classmethod
    def new(cls,
            topic: str,
            sender_id: int,
            recipient_ids: List[int],
            initial_message: str) -> Optional['PMConversation']:
        """
        Create a private message object, set states for the sender and receiver,
        and create the initial message.
        """
        User.is_valid(sender_id, error=True)
        for rid in recipient_ids:
            User.is_valid(rid, error=True)
        pm_conversation = super()._new(topic=topic)
        for user_id in (sender_id, *recipient_ids):
            PMConversationState.new(
                conv_id=pm_conversation.id,
                user_id=user_id)
        PMMessage.new(
            conv_id=pm_conversation.id,
            user_id=user_id,
            contents=initial_message)
        return pm_conversation

    @property
    def messages(self):
        if not hasattr(self, '_messages'):
            self._messages = PMMessage.from_conversation(self.id)
        return self._messages

    @property
    def users(self):
        return PMConversationState.get_users_in_conversation(self.conv_id)

    def set_state(self, user_id):
        """
        Assign the state of the PM for a user to attributes of this object. This makes
        the object suitable for serialization.
        """
        self._conv_state = PMConversationState.from_attrs(
            conv_id=self.id,
            user_id=user_id)
        if not self._conv_state:
            raise PMStateNotFound
        self.read = self._conv_state.read
        self.sticky = self._conv_state.sticky

    def set_messages(self,
                     page: int = 1,
                     limit: int = 50) -> None:
        self._messages = PMMessage.from_conversation(self.id, page, limit)

    def belongs_to_user(self) -> bool:
        """
        Override of base class method to check against all users with a conversation state.
        """
        return flask.g.user is not None and flask.g.user.id in {u.id for u in self.users}


class PMConversationState(db.Model, MultiPKMixin):
    __tablename__ = 'pm_conversations_state'
    __cache_key__ = 'pm_convesations_state_{conv_id}_{user_id}'
    __cache_key_members__ = 'pm_conversations_state_{conv_id}_members'

    conv_id = db.Column(db.Integer, db.ForeignKey('pm_conversations.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    read = db.Column(db.Boolean, nullable=False, server_default='f')
    sticky = db.Column(db.Boolean, nullable=False, server_default='f', index=True)
    deleted = db.Column(db.Boolean, nullable=False, server_default='f', index=True)
    time_added = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    @classmethod
    def get_users_in_conversation(cls, conv_id: int) -> List[User]:
        return cls.get_many(
            key=cls.__cache_key_members__.format(conv_id=conv_id),
            filter=cls.conv_id == conv_id,
            order=cls.time_added.asc())

    @hybrid_property
    def in_inbox(cls):
        return select(exists().where(and_(
            PMMessage.conv_id == cls.conv_id,
            PMMessage.user_id != cls.user_id,
            cls.deleted == 'f',
            ))).as_scalar()
        pass

    @hybrid_property
    def in_sentbox(cls):
        return select(exists().where(and_(
            PMMessage.conv_id == cls.conv_id,
            PMMessage.user_id == cls.user_id,
            cls.deleted == 'f',
            ))).as_scalar()

    @classmethod
    def new(cls,
            conv_id: int,
            user_id: int) -> Optional['PMConversationState']:
        """
        Create a private message object, set states for the sender and receiver,
        and create the initial message.
        """
        PMConversation.is_valid(conv_id, error=True)
        User.is_valid(user_id, error=True)
        return super()._new(
            conv_id=conv_id,
            user_id=user_id)


class PMMessage(db.Model, SinglePKMixin):
    __tablename__ = 'pm_messages'
    __cache_key__ = 'pm_messages_{id}'
    __cache_key_of_conversation__ = 'pm_messages_conv_{conv_id}'
    __serializer__ = PMMessageSerializer

    id = db.Column(db.Integer, primary_key=True)
    conv_id = db.Column(
        db.Integer, db.ForeignKey('pm_conversations.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
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
        return super()._new(
            conv_id=conv_id,
            user_id=user_id,
            contents=contents)
