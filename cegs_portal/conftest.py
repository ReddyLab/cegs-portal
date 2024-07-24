import json
from typing import Optional

import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from django.db.models import Model
from django.test import Client, RequestFactory


class Response:
    def __init__(self, response):
        self.resp = response

    def json(self):
        return json.loads(self.resp.content)

    def __getattr__(self, method_name):
        return self.resp.__getattribute__(method_name)


class Request:
    def __init__(self, request):
        self.req = request

    def request(self, view, *args, **kwargs):
        return Response(view(self.req, *args, **kwargs))


class RequestBuilder:
    def __init__(
        self,
        user_model: Optional[Model] = None,
        group_model: Optional[Model] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        is_portal_admin: bool = False,
        permissions: Optional[list[str]] = None,
    ):
        self.request_factory = RequestFactory()
        self.username = username
        self.password = password

        if user_model is not None and username is not None and password is not None:
            self.user = user_model.objects.create_user(username=username, password=password)
            self.user.is_portal_admin = is_portal_admin
            self.user.save()
        else:
            self.user = AnonymousUser()

        if permissions is not None and self.user is not None:
            perm_objs = list(Permission.objects.filter(codename__in=permissions).all())
            self.user.user_permissions.add(*perm_objs)

        if group_model is not None:
            assert not isinstance(self.user, AnonymousUser)
            self.group = group_model
            self.user.groups.add(group_model.group)
        else:
            self.group = None

    def get(self, *args, **kwargs):
        request = self.request_factory.get(*args, **kwargs)
        request.user = self.user

        return Request(request)

    def post(self, *args, **kwargs):
        request = self.request_factory.post(*args, **kwargs)
        request.user = self.user

        return Request(request)

    def set_user_experiments(self, experiment_list: list[str]):
        if isinstance(self.user, AnonymousUser):
            return

        self.user.experiments = experiment_list
        self.user.save()

    def set_group_experiments(self, experiment_list: list[str]):
        if self.group is None:
            return

        self.group.experiments = experiment_list
        self.group.save()

    def add_user_experiment_collection(self, experiment_collection: str):
        if isinstance(self.user, AnonymousUser):
            return

        self.user.experiment_collections.append(experiment_collection)
        self.user.save()

    def add_group_experiment_collection(self, experiment_collection: str):
        if self.group is None:
            return

        self.group.experiment_collections.append(experiment_collection)
        self.group.save()


@pytest.fixture
def public_test_client():
    return RequestBuilder()


@pytest.fixture
def login_test_client(django_user_model):
    return RequestBuilder(user_model=django_user_model, username="user2", password="bar")


@pytest.fixture
def portal_admin_test_client(django_user_model):
    return RequestBuilder(user_model=django_user_model, username="user2", password="bar", is_portal_admin=True)


@pytest.fixture
def group_login_test_client(django_user_model, group_extension):  # noqa: F811
    return RequestBuilder(user_model=django_user_model, group_model=group_extension, username="user3", password="bar")


class SearchClient:
    def __init__(
        self,
        user_model: Optional[Model] = None,
        group_model: Optional[Model] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        is_portal_admin: bool = False,
        permissions: Optional[list[str]] = None,
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

        if permissions is not None and self.user is not None:
            perm_objs = list(Permission.objects.filter(codename__in=permissions).all())
            self.user.user_permissions.add(*perm_objs)

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

    def add_user_experiment_collection(self, experiment_collection: str):
        if self.user is None:
            return

        self.user.experiment_collections.append(experiment_collection)
        self.user.save()

    def add_group_experiment_collection(self, experiment_collection: str):
        if self.group is None:
            return

        self.group.experiment_collections.append(experiment_collection)
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
def group_login_client(django_user_model, group_extension):  # noqa: F811
    return SearchClient(user_model=django_user_model, group_model=group_extension, username="user3", password="bar")
