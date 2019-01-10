# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from shuup.admin.forms import ShuupAdminForm
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.picotable import Column
from shuup.admin.utils.views import CreateOrUpdateView, PicotableListView
from shuup.core.models import Label


class LabelListView(PicotableListView):
    model = Label
    url_identifier = "label"

    default_columns = [
        Column("identifier", _("Identifier")),
        Column("name", _("Name")),
        Column("created_on", _("Created on")),
        Column("modified_on", _("Modified on")),
    ]


class LabelForm(ShuupAdminForm):
    class Meta:
        model = Label
        exclude = ()


class LabelEditView(CreateOrUpdateView):
    model = Label
    form_class = LabelForm
    template_name = "shuup/admin/labels/edit.jinja"
    context_object_name = "label"

    def get_toolbar(self):
        object = self.get_object()
        delete_url = (
            reverse_lazy("shuup_admin:label.delete", kwargs={"pk": object.pk})
            if object.pk else None)
        return get_default_edit_toolbar(self, self.get_save_form_id(), delete_url=delete_url)


class LabelDeleteView(DetailView):
    model = Label

    def post(self, request, *args, **kwargs):
        label = self.get_object()
        label.delete()
        messages.success(request, _("%s has been deleted.") % label)
        return HttpResponseRedirect(reverse_lazy("shuup_admin:label.list"))
