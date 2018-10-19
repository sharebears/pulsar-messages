import messages
from core.conftest import *  # noqa: F401, F403
from core.conftest import PLUGINS, POPULATORS
from messages.test_data import MessagesPopulator

PLUGINS.append(messages)
POPULATORS.append(MessagesPopulator)
