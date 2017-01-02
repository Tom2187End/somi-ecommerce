# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum

from shuup.apps.provides import get_provide_objects


class ImportMode(Enum):
    CREATE_UPDATE = "create,update"
    CREATE = "create"
    UPDATE = "update"

    class Labels:
        CREATE_UPDATE = _("Allow create and update")
        CREATE = _("Only create (no updates)")
        UPDATE = _("Only update existing (no new ones are created)")


def get_importer_choices():
    return [(i.identifier, i.name) for i in get_provide_objects("importers")]


def get_importer(identifier):
    for i in get_provide_objects("importers"):
        if i.identifier == identifier:
            return i
    return None


def get_import_file_path(filename):
    return os.path.join(settings.MEDIA_ROOT, "import_temp", os.path.basename(filename))
