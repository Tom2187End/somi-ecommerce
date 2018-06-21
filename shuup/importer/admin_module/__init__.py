# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.utils.urls import admin_url


class ImportAdminModule(AdminModule):
    name = _("Data Import")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:importer.import")

    def get_urls(self):
        return [
            admin_url(
                "^importer/import$",
                "shuup.importer.admin_module.import_views.ImportView",
                name="importer.import",
                permissions=["shuup.change_shop"]
            ),
            admin_url(
                "^importer/import/process$",
                "shuup.importer.admin_module.import_views.ImportProcessView",
                name="importer.import_process",
                permissions=["shuup.change_shop"]
            ),
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Data Import"),
                category=SETTINGS_MENU_CATEGORY,
                subcategory="data_transfer",
                url="shuup_admin:importer.import",
                icon="fa fa-star"
            )
        ]
