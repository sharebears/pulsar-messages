from core import db
from core.mixins import TestDataPopulator
from messages.models import PMConversation, PMConversationState, PMMessage


class MessagesPopulator(TestDataPopulator):

    @classmethod
    def populate(cls):
        pm_1 = PMConversation.new(
            topic='New Private Message!',
            sender_id=1,
            recipient_ids=[2],
            initial_message='boi')
        pm_2 = PMConversation.new(
            topic='New Group Message!',
            sender_id=3,
            recipient_ids=[1, 2],
            initial_message='i hate you both!')
        pm_3 = PMConversation.new(
            topic='New Group Message!',
            sender_id=1,
            recipient_ids=[3, 2],
            initial_message='i love love love you!')
        PMMessage.new(
            conv_id=pm_1.id,
            user_id=2,
            contents='gal')
        PMMessage.new(
            conv_id=pm_2.id,
            user_id=3,
            contents='a lot!')
        PMConversationState.from_attrs(
            conv_id=pm_3.id,
            user_id=3).deleted = True
        db.session.commit()

    @classmethod
    def unpopulate(cls):
        db.engine.execute('DELETE FROM pm_messages')
        db.engine.execute('DELETE FROM pm_conversations_state')
        db.engine.execute('DELETE FROM pm_conversations')
        db.engine.execute('ALTER SEQUENCE pm_messages_id_seq RESTART WITH 1')
        db.engine.execute('ALTER SEQUENCE pm_conversations_id_seq RESTART WITH 1')