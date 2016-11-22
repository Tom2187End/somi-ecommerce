# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from django.core.management import call_command
from six import StringIO


@pytest.mark.django_db
def test_makemigrations():
    if type(settings.MIGRATION_MODULES).__name__ == "DisableMigrations":
        pytest.skip()
    out = StringIO()
    call_command("shuup_makemigrations", "shuup", "--dry-run", stdout=out)
    assert "No changes detected in app 'shuup'" in out.getvalue()
