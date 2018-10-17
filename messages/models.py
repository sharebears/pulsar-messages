from core import db
from sqlalchemy import func
from core.mixins import SinglePKMixin, MultiPKMixin


class PMConversation(db.Model, SinglePKMixin):
    __tablename__ = 'pm_conversations'
    __cache_key__ = 'pm_conversation_{id}'

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(128), nullable=False)


class PMConversationOfUser(db.Model, MultiPKMixin):
    __tablename__ = 'pm_conversations_users'
    __cache_key__ = 'pm_convesations_users_{conv_id}_{user_id}'

    conv_id = db.Column(db.Integer, db.ForeignKey('pm_conversations.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    in_inbox = db.Column(db.Boolean, nullable=False, index=True)
    in_sentbox = db.Column(db.Boolean, nullable=False, index=True)
    time = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    read = db.Column(db.Boolean, nullable=False, server_default='f')
    sticky = db.Column(db.Boolean, nullable=False, server_default='f', index=True)


class PMMessages(db.Model, SinglePKMixin):
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


class PMForwards(db.Model, MultiPKMixin):
    __tablename__ = 'pm_forwards'

    conv_id = db.Column(db.Integer, db.ForeignKey('pm_conversations.id'), primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
