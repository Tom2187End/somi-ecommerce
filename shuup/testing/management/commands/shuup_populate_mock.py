# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from optparse import make_option

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import translation

from shuup.testing.mock_population import Populator


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--with-superuser", default=None),
    )

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGES[0][0])
        superuser_name = options.get("with_superuser")
        if superuser_name:
            filter_params = {get_user_model().USERNAME_FIELD: superuser_name}
            user = get_user_model().objects.filter(**filter_params).first()
            if not user:
                user = get_user_model().objects.create_superuser(
                    username=superuser_name,
                    email="%s@shuup.local" % superuser_name,
                    password=superuser_name,
                )
                print("Superuser created: %s" % user)
            else:
                print("Superuser pre-existed: %s" % user)
        Populator().populate()
