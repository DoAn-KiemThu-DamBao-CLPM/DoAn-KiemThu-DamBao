import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
pytest_plugins = ["framework.reporter"]

from framework import db                       # noqa: E402
from framework.client import AnynClient        # noqa: E402
from framework.config import ADMIN, ALICE, BOB, CAROL  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_login_attempts():
    """Failed-login throttling is per IP (all tests share 127.0.0.1): start every test with a clean slate."""
    db.clear_login_attempts()
    yield


@pytest.fixture
def guest():
    return AnynClient()


@pytest.fixture
def user():
    return AnynClient.new_user("qa")


@pytest.fixture
def user2():
    return AnynClient.new_user("qb")


@pytest.fixture
def premium():
    return AnynClient.new_user("qp", spent=25)


@pytest.fixture
def admin():
    return AnynClient.as_(ADMIN)


@pytest.fixture
def alice():
    return AnynClient.as_(ALICE)


@pytest.fixture
def bob():
    return AnynClient.as_(BOB)
