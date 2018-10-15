import pytest

import messages
from core import db
from core.conftest import *  # noqa: F401, F403
from core.conftest import PLUGINS, UNPOPULATE_FUNCTIONS


@pytest.fixture(autouse=True)
def populate_db_(app, client):
    pass


def unpopulate_database():
    db.engine.execute("DELETE FROM some_table")


PLUGINS.append(messages)
UNPOPULATE_FUNCTIONS.append(unpopulate_database)
