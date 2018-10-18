from core import db
from core.mixins import TestDataPopulator
from messages.permissions import PMPermissions


class MessagesPopulator(TestDataPopulator):

    @classmethod
    def populate(cls):
        db.session.execute(
            """
            INSERT INTO pm_conversations (topic) VALUES
            ('New Private Message!'),
            ('New Group Message!'),
            ('New Group Message!'),
            ('detingstings')
            """)
        db.session.execute(
            """
            INSERT INTO pm_conversations_state (conv_id, user_id, read, sticky, deleted) VALUES
            (1, 1, 'f', 'f', 'f'), (1, 2, 'f', 'f', 'f'),
            (2, 1, 't', 't', 'f'), (2, 2, 'f', 'f', 'f'), (2, 3, 'f', 'f', 'f'),
            (3, 1, 'f', 'f', 'f'), (3, 2, 'f', 'f', 'f'), (3, 3, 'f', 'f', 't'),
            (4, 2, 'f', 'f', 'f'), (4, 3, 'f', 'f', 'f')
            """)
        db.session.execute(
            """
            INSERT INTO pm_messages (conv_id, user_id, contents) VALUES
            (1, 1, 'boi'),
            (2, 3, 'i hate you both!'),
            (3, 1, 'i love love love you!'),
            (4, 1, 'testing'),
            (1, 2, 'gal'),
            (2, 3, 'a lot!')
            """)
        cls.add_permissions(
            PMPermissions.VIEW,
            PMPermissions.CREATE,
            PMPermissions.SEND,
            PMPermissions.DELETE)
        db.session.commit()

    @classmethod
    def unpopulate(cls):
        db.engine.execute('DELETE FROM pm_messages')
        db.engine.execute('DELETE FROM pm_conversations_state')
        db.engine.execute('DELETE FROM pm_conversations')
        db.engine.execute('ALTER SEQUENCE pm_conversations_id_seq RESTART WITH 1')
        db.engine.execute('ALTER SEQUENCE pm_messages_id_seq RESTART WITH 1')
