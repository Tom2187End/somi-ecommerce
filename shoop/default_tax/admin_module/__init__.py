# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from shoop.admin.base import AdminModule, MenuEntry
from shoop.admin.utils.urls import admin_url, derive_model_url
from shoop.default_tax.models import TaxRule


class DefaultTaxAdminModule(AdminModule):
    name = _("Default Tax Module")
    category = _("Taxes")
    breadcrumbs_menu_entry = MenuEntry(category, "shoop_admin:default_tax.tax_rule.list")

    def get_urls(self):
        return [
            admin_url(
                "default-tax/rules/(?P<pk>\d+)/",
                "shoop.default_tax.admin_module.views.TaxRuleEditView",
                name="default_tax.tax_rule.edit"
            ),
            admin_url(
                "default-tax/rules/new/",
                "shoop.default_tax.admin_module.views.TaxRuleEditView",
                kwargs={"pk": None},
                name="default_tax.tax_rule.new"
            ),
            admin_url(
                "default-tax/rules/",
                "shoop.default_tax.admin_module.views.TaxRuleListView",
                name="default_tax.tax_rule.list"
            ),
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("List Tax Rules"), icon="fa fa-file-text",
                url="shoop_admin:default_tax.tax_rule.list",
                category=self.category, aliases=[_("Show tax rules")]
            )
        ]

    def get_model_url(self, object, kind):
        return derive_model_url(TaxRule, "shoop_admin:default_tax.tax_rule", object, kind)
