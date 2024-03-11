from enum import Enum

from django.contrib.auth.models import AbstractUser, Group
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import BooleanField, CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class UserType(Enum):
    ANONYMOUS = 1
    ADMIN = 2
    LOGGED_IN = 3


class User(AbstractUser):
    """Default user for CEGS CCGR Portal."""

    #: First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore

    experiments = ArrayField(CharField(_("Associated Experiments"), max_length=17), default=list)
    is_portal_admin = BooleanField(_("Is User a Portal Admin"), default=False)

    def get_full_name(self):
        return self.name.strip()

    def get_short_name(self):
        return self.name.strip()

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    def all_experiments(self):
        self_experiments = self.experiments
        group_experiments = (
            User.objects.filter(username=self.username)
            .prefetch_related("groups__groupextension__experiments")
            .values_list("groups__groupextension__experiments", flat=True)[0]
        )
        if group_experiments is None:
            return self_experiments
        else:
            return self_experiments + group_experiments


# This might seem like an awkard way to extend the Group model, but that's only because it is.
# There is not currently a simple way to create a custom group model and use it for auth in the
# same way one can with users (by setting AUTH_USER_MODEL in settings.py)
#
# Maybe someday there will be an AUTH_GROUP_MODEL: https://code.djangoproject.com/ticket/29748
class GroupExtension(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    description = CharField(_("Group Description"), max_length=1024, null=True)
    experiments = ArrayField(CharField(_("Associated Experiments"), max_length=17), default=list)
