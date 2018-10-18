import messages
from messages.test_data import MessagesPopulator
from core.conftest import *  # noqa: F401, F403
from core.conftest import PLUGINS, POPULATORS

PLUGINS.append(messages)
POPULATORS.append(MessagesPopulator)
