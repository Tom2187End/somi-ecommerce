# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import os

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry, Notification
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.modules.sample_data import manager as sample_manager
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.admin.utils.urls import admin_url
from shuup.core.models import Shop
from shuup.core.settings_provider import ShuupSettings

SAMPLE_BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SAMPLE_IMAGES_BASE_DIR = os.path.join(SAMPLE_BASE_DIR, "sample_data/images")


class SampleDataAdminModule(AdminModule):
    def get_urls(self):
        return [
            admin_url(
                "^sample_data/$",
                "shuup.admin.modules.sample_data.views.ConsolidateSampleObjectsView",
                name="sample_data",
                permissions=get_default_model_permissions(Shop)
            )
        ]

    def get_menu_entries(self, request):
        # not supported
        if ShuupSettings.get_setting("SHUUP_ENABLE_MULTIPLE_SHOPS"):
            return []

        return [
            MenuEntry(
                text="Sample Data",
                category=SETTINGS_MENU_CATEGORY,
                subcategory="data_transfer",
                url="shuup_admin:sample_data",
                icon="fa fa-star"
            )
        ]

    def get_required_permissions(self):
        return get_default_model_permissions(Shop)

    def get_notifications(self, request):
        """ Injects a message to the user and also a notification """
        # multi-shop not supported
        if not ShuupSettings.get_setting("SHUUP_ENABLE_MULTIPLE_SHOPS"):
            # there would be only sample data for single-shops envs
            shop = Shop.objects.first()

            if sample_manager.has_installed_samples(shop):
                messages.warning(request, _('There is sample data installed. '
                                            'Access "Settings > Sample Data" for more information.'))

                yield Notification(
                    _("There is sample data installed. Click here to consolidate or delete them."),
                    title=_("Sample Data"),
                    kind="warning",
                    url="shuup_admin:sample_data"
                )
