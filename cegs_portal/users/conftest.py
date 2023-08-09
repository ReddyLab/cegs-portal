import pytest

from cegs_portal.users.models import GroupExtension, User
from cegs_portal.users.tests.factories import GroupExtensionFactory, UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> User:
    return UserFactory()


@pytest.fixture
def group_extension() -> GroupExtension:
    return GroupExtensionFactory()
