from core import db, cache
from typing import Optional, List
from sqlalchemy import func, select, and_, exists
from sqlalchemy.ext.hybrid import hybrid_property
from messages.exceptions import PMStateNotFound
from core.mixins import SinglePKMixin, MultiPKMixin
from core.users.models import User


class PMConversation(db.Model, SinglePKMixin):
    __tablename__ = 'pm_conversations'
    __cache_key__ = 'pm_conversation_{id}'

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(128), nullable=False)
    last_updated_time = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    @classmethod
    def new(cls,
            topic: str,
            sender_id: int,
            recipient_id: int,
            initial_message: str) -> Optional['PMConversation']:
        """
        Create a private message object, set states for the sender and receiver,
        and create the initial message.
        """
        User.is_valid(sender_id, error=True)
        User.is_valid(recipient_id, error=True)
        pm_conversation = super()._new(topic=topic)
        for user_id in [sender_id, recipient_id]:
            PMConversationState.new(
                conv_id=pm_conversation.id,
                user_id=user_id)
        PMMessage.new(
            conv_id=pm_conversation.id,
            user_id=user_id,
            contents=initial_message)
        return pm_conversation

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
        self.recipient = self._conv_state.recipient

    @property
    def messages(self):
        if not hasattr(self, '_messages'):
            self._messages = PMMessage.from_conversation(self.id)
        return self._messages

    def set_messages(self,
                     page: int = 1,
                     limit: int = 50) -> None:
        self._messages = PMMessage.from_conversation(self.id, page, limit)


class PMConversationState(db.Model, MultiPKMixin):
    __tablename__ = 'pm_conversations_state'
    __cache_key__ = 'pm_convesations_state_{conv_id}_{user_id}'
    __cache_key_recipient__ = 'pm_conversations_state_{conv_id}_{user_id}_recipient'

    conv_id = db.Column(db.Integer, db.ForeignKey('pm_conversations.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    read = db.Column(db.Boolean, nullable=False, server_default='f')
    sticky = db.Column(db.Boolean, nullable=False, server_default='f', index=True)

    @hybrid_property
    def in_inbox(cls):
        return select(exists().where(and_(
            PMMessage.conv_id == cls.conv_id,
            PMMessage.user_id != cls.user_id,
            ))).as_scalar()
        pass

    @hybrid_property
    def in_sentbox(cls):
        return select(exists().where(and_(
            PMMessage.conv_id == cls.conv_id,
            PMMessage.user_id == cls.user_id,
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

    @property
    def recipient(self):
        cache_key = self.__cache_key_recipient__.format(conv_id=self.conv_id, user_id=self.user_id)
        recipient_id = cache.get(cache_key)
        if not recipient_id:
            recipient_id = db.session.query(PMConversationState.user_id).where(and_(
                PMConversationState.conv_id == self.conv_id,
                PMConversationState.user_id != self.user_id,
                )).scalar()
            cache.set(cache_key, recipient_id, timeout=3600 * 24 * 28)
        return User.from_pk(recipient_id)


class PMMessage(db.Model, SinglePKMixin):
    __tablename__ = 'pm_messages'
    __cache_key__ = 'pm_messages_{id}'
    __cache_key_of_conversation__ = 'pm_messages_conv_{conv_id}'

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


class PMForward(db.Model, MultiPKMixin):
    __tablename__ = 'pm_forwards'

    conv_id = db.Column(db.Integer, db.ForeignKey('pm_conversations.id'), primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
