# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.conf import settings
from django.db import models
from enumfields import Enum, EnumIntegerField
from django.utils.encoding import force_text
from jsonfield import JSONField
from django.utils.translation import ugettext_lazy as _


class LogEntryKind(Enum):
    OTHER = 0
    AUDIT = 1
    EDIT = 2
    DELETION = 3
    NOTE = 4
    EMAIL = 5
    WARNING = 6
    ERROR = 7

    class Labels:
        OTHER = _("other")
        AUDIT = _("audit")
        EDIT = _("edit")
        DELETION = _("deletion")
        NOTE = _("note")
        EMAIL = _("email")
        WARNING = _("warning")
        ERROR = _("error")


class BaseLogEntry(models.Model):
    target = None  # This will be overridden dynamically
    created_on = models.DateTimeField(auto_now_add=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    message = models.CharField(max_length=256)
    identifier = models.CharField(max_length=64, blank=True)
    kind = EnumIntegerField(LogEntryKind, default=LogEntryKind.OTHER)
    extra = JSONField(null=True, blank=True)

    class Meta:
        abstract = True


all_known_log_models = {}


def define_log_model(model_class):
    log_model_name = "%sLogEntry" % model_class.__name__

    class Meta:
        app_label = model_class._meta.app_label
        abstract = False

    class_dict = {
        "target": models.ForeignKey(model_class, related_name="log_entries"),
        "__module__": model_class.__module__,
        "Meta": Meta,
        "logged_model": model_class,
    }

    log_entry_class = type(str(log_model_name), (BaseLogEntry, ), class_dict)

    def _add_log_entry(self, message, identifier=None, kind=LogEntryKind.OTHER, user=None, extra=None, save=True):
        # You can also pass something that contains "user" as an
        # attribute for an user
        user = (getattr(user, "user", user) or None)
        if not getattr(user, "pk", None):
            user = None
        log_entry = log_entry_class(
            target=self,
            message=message,
            identifier=force_text(identifier or "", errors="ignore")[:64],
            user=user,
            kind=kind,
            extra=(extra or None),
        )
        if save:
            log_entry.save()
        return log_entry

    setattr(model_class, "add_log_entry", _add_log_entry)
    all_known_log_models[model_class] = log_entry_class
    return log_entry_class
