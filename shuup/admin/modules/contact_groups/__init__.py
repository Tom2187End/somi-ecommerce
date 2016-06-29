# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.admin.utils.urls import (
    admin_url, derive_model_url, get_edit_and_list_urls
)
from shuup.core.models import ContactGroup


class ContactGroupModule(AdminModule):
    name = _("Contact Groups")
    category = _("Contacts")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:contact-group.list")

    def get_urls(self):
        return [
            admin_url(
                "^contact-group/(?P<pk>\d+)/delete/$",
                "shuup.admin.modules.contact_groups.views.ContactGroupDeleteView",
                name="contact-group.delete",
                permissions=["shuup.delete_contactgroup"],
            )
        ] + get_edit_and_list_urls(
            url_prefix="^contact-groups",
            view_template="shuup.admin.modules.contact_groups.views.ContactGroup%sView",
            name_template="contact-group.%s",
            permissions=get_default_model_permissions(ContactGroup),
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-asterisk",
                url="shuup_admin:contact-group.list",
                category=self.category
            ),
        ]

    def get_required_permissions(self):
        return get_default_model_permissions(ContactGroup)

    def get_model_url(self, object, kind):
        return derive_model_url(ContactGroup, "shuup_admin:contact-group", object, kind)
