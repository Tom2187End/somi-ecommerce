# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.template import engines
from django.utils.translation import ugettext_lazy as _
from django_jinja.backend import Jinja2

from shoop.admin.base import AdminModule, MenuEntry, Notification
from shoop.admin.utils.urls import admin_url
from shoop.xtheme.engine import XthemeEnvironment
from shoop.xtheme.theme import get_current_theme


class XthemeAdminModule(AdminModule):
    """
    Admin module for Xtheme.

    Allows theme activation/deactivation and further configuration.
    """
    name = _("Shoop Extensible Theme Engine")
    breadcrumbs_menu_entry = MenuEntry(_("Themes"), "shoop_admin:xtheme.config")

    def get_urls(self):  # doccov: ignore
        return [
            admin_url(
                "^xtheme/(?P<theme_identifier>.+?)/",
                "shoop.xtheme.admin_module.views.ThemeConfigDetailView",
                name="xtheme.config_detail"
            ),
            admin_url(
                "^xtheme/",
                "shoop.xtheme.admin_module.views.ThemeConfigView",
                name="xtheme.config"
            )
        ]

    def get_menu_category_icons(self):
        return {self.name: "fa fa-paint-brush"}

    def get_menu_entries(self, request):  # doccov: ignore
        return [
            MenuEntry(
                text=_("Themes"), icon="fa fa-paint-brush",
                url="shoop_admin:xtheme.config",
                category=self.name
            )
        ]

    def get_notifications(self, request):
        try:
            engine = engines["jinja2"]
        except KeyError:
            engine = None

        if engine and isinstance(engine, Jinja2):  # The engine is what we expect...
            if isinstance(engine.env, XthemeEnvironment):  # ... and it's capable of loading themes...
                if not get_current_theme(request):  # ... but there's no theme active?!
                    # Panic!
                    yield Notification(
                        text=_("No theme is active. Click here to activate one."),
                        title=_("Theming"),
                        url="shoop_admin:xtheme.config"
                    )
