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
from shuup.admin.menu import CAMPAIGNS_MENU_CATEGORY
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shuup.discounts.models import HappyHour


class HappyHourModule(AdminModule):
    name = _("Discounts Happy Hours")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:discounts_happy_hour.list")

    def get_urls(self):
        from shuup.admin.urls import admin_url
        delete = admin_url(
            "^discounts_happy_hour/(?P<pk>\d+)/delete/$",
            "shuup.discounts.admin.views.HappyHourDeleteView",
            name="discounts_happy_hour.delete",
            permissions=get_default_model_permissions(HappyHour)
        )

        return [delete] + get_edit_and_list_urls(
            url_prefix="^discounts_happy_hour",
            view_template="shuup.discounts.admin.views.HappyHour%sView",
            name_template="discounts_happy_hour.%s",
            permissions=get_default_model_permissions(HappyHour)
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Product Discounts Happy Hours"),
                icon="fa fa-percentage",
                url="shuup_admin:discounts_happy_hour.list",
                category=CAMPAIGNS_MENU_CATEGORY,
                ordering=7
            )
        ]

    def get_required_permissions(self):
        return get_default_model_permissions(HappyHour)

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(HappyHour, "shuup_admin:discounts_happy_hour", object, kind)
