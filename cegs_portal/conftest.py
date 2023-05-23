from typing import Optional

import pytest
from django.db.models import Model
from django.test import Client


class SearchClient:
    def __init__(
        self,
        user_model: Optional[Model] = None,
        group_model: Optional[Model] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        is_portal_admin: bool = False,
    ):
        self.client = Client()
        self.username = username
        self.password = password

        if user_model is not None and username is not None and password is not None:
            self.user = user_model.objects.create_user(username=username, password=password)
            self.user.is_portal_admin = is_portal_admin
            self.user.save()
            self.client.login(username=username, password=password)
        else:
            self.user = None

        if group_model is not None:
            assert user_model is not None
            self.group = group_model
            self.user.groups.add(group_model.group)
        else:
            self.group = None

    def get(self, *args, **kwargs):
        return self.client.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.client.post(*args, **kwargs)

    def set_user_experiments(self, experiment_list: list[str]):
        if self.user is None:
            return

        self.user.experiments = experiment_list
        self.user.save()

    def set_group_experiments(self, experiment_list: list[str]):
        if self.group is None:
            return

        self.group.experiments = experiment_list
        self.group.save()


@pytest.fixture
def public_client():
    return SearchClient()


@pytest.fixture
def login_client(django_user_model):
    return SearchClient(user_model=django_user_model, username="user2", password="bar")


@pytest.fixture
def portal_admin_client(django_user_model):
    return SearchClient(user_model=django_user_model, username="user2", password="bar", is_portal_admin=True)


@pytest.fixture
def group_login_client(django_user_model, group_extension):  # # noqa: F811
    return SearchClient(user_model=django_user_model, group_model=group_extension, username="user3", password="bar")
