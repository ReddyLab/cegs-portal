from typing import Any, Sequence

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from factory import Faker, post_generation
from factory.django import DjangoModelFactory

from cegs_portal.users.models import GroupExtension


class UserFactory(DjangoModelFactory):

    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")
    experiments: list[str] = []
    is_portal_admin = Faker("boolean", chance_of_getting_true=10)

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]


class GroupFactory(DjangoModelFactory):
    name = Faker("name")

    class Meta:
        model = Group
        django_get_or_create = ["name"]

    @post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for permission in extracted:
                self.permissions.add(permission)  # pylint: disable=no-member


class GroupExtensionFactory(DjangoModelFactory):
    description = Faker("text", max_nb_chars=1024)
    experiments: list[str] = []

    class Meta:
        model = GroupExtension

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)

        group = kwargs.get("group", None)
        if group is not None:
            obj.group = group
        else:
            obj.group = GroupFactory()

        obj.save()
        return obj
