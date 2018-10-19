from core import db
from core.mixins import TestDataPopulator
from messages.permissions import PMPermissions


class MessagesPopulator(TestDataPopulator):

    @classmethod
    def populate(cls):
        db.session.execute(
            """
            INSERT INTO pm_conversations (topic, sender_id) VALUES
            ('New Private Message!', 1),
            ('New Group Message!', 3),
            ('New Group Message!', 1),
            ('detingstings', 2)
            """)
        db.session.execute(
            """
            INSERT INTO pm_conversations_state (
                conv_id, user_id, read, sticky, deleted, last_response_time
            ) VALUES
            (1, 1, 'f', 'f', 'f', NOW() - INTERVAL '2 DAYS'),
            (1, 2, 'f', 'f', 'f', NOW() - INTERVAL '3 DAYS'),
            (2, 1, 't', 't', 'f', NOW() - INTERVAL '1 DAY'),
            (2, 2, 'f', 'f', 'f', NOW() - INTERVAL '1 DAY'),
            (2, 3, 'f', 'f', 'f', NULL),
            (3, 1, 'f', 'f', 'f', NULL),
            (3, 2, 'f', 'f', 'f', NOW() - INTERVAL '12 HOURS'),
            (3, 3, 'f', 'f', 't', NOW() - INTERVAL '12 HOURS'),
            (4, 2, 'f', 'f', 'f', NULL),
            (4, 3, 'f', 'f', 'f', NOW())
            """)
        db.session.execute(
            """
            INSERT INTO pm_messages (conv_id, user_id, contents, time) VALUES
            (1, 1, 'boi', NOW() - INTERVAL '3 DAYS'),
            (1, 2, 'gal', NOW() - INTERVAL '2 DAYS'),
            (2, 3, 'i hate you both!', NOW() - INTERVAL '2 DAYS'),
            (2, 3, 'a lot!', NOW() - INTERVAL '1 DAY'),
            (3, 1, 'i love love love you!', NOW() - INTERVAL '12 HOURS'),
            (4, 2, 'testing', NOW())
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
