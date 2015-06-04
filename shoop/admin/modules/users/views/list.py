# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.views.generic import ListView
from shoop.admin.toolbar import Toolbar, NewActionButton
from shoop.admin.utils.picotable import PicotableViewMixin, Column, true_or_false_filter, TextFilter


class UserListView(PicotableViewMixin, ListView):
    model = settings.AUTH_USER_MODEL
    columns = [
        Column("username", _(u"Username"), filter_config=TextFilter()),
        Column("email", _(u"Email"), filter_config=TextFilter()),
        Column("first_name", _(u"First Name"), filter_config=TextFilter()),
        Column("last_name", _(u"Last Name"), filter_config=TextFilter()),
        Column("is_active", _(u"Active"), filter_config=true_or_false_filter),
        Column("is_staff", _(u"Staff"), filter_config=true_or_false_filter),
        Column("is_superuser", _(u"Superuser"), filter_config=true_or_false_filter),
    ]

    def get_queryset(self):
        return get_user_model().objects.all()

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context["toolbar"] = Toolbar([NewActionButton("shoop_admin:user.new")])
        context["title"] = force_text(get_user_model()._meta.verbose_name_plural).title()
        return context

    def get_object_abstract(self, instance, item):
        bits = filter(None, [
            _("First Name: %s") % (instance.first_name or "\u2014"),
            _("Last Name: %s") % (instance.last_name or "\u2014"),
            _("Active") if instance.is_active else _(u"Inactive"),
            _("Email: %s") % (instance.email or "\u2014"),
            _("Staff") if instance.is_staff else None,
            _("Superuser") if instance.is_superuser else None
        ])
        return [
            {"text": instance.username or _("User"), "class": "header"},
            {"text": ", ".join(bits)}
        ]
