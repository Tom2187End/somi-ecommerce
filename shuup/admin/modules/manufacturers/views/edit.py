# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.db.models import Q
from django.forms.models import ModelForm
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.core.models import Manufacturer, Shop


class ManufacturerForm(ModelForm):
    class Meta:
        model = Manufacturer
        exclude = ("identifier", "created_on")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(ManufacturerForm, self).__init__(*args, **kwargs)

        # add shops field when superuser only
        if getattr(self.request.user, "is_superuser", False):
            initial_shops = []
            if self.instance.pk:
                initial_shops = self.instance.shops.all()

            self.fields["shops"] = Select2MultipleField(
                label=_("Shops"),
                help_text=_("Select shops for this manufacturer. Keep it blank to share with all shops."),
                model=Shop,
                initial=initial_shops,
                required=False,
            )
            self.fields["shops"].widget.choices = [(shop.pk, force_text(shop)) for shop in initial_shops]
        else:
            # drop shops fields
            self.fields.pop("shops", None)

    def save(self, commit=True):
        is_superuser = getattr(self.request.user, "is_superuser", False)

        # do not let any user to change shared Manufacturers
        if self.instance.pk and self.instance.shops.count() == 0 and not is_superuser:
            raise forms.ValidationError(_("You have no permission to change a shared Manufacturer."))

        instance = super(ManufacturerForm, self).save(commit)

        # if shops field is not available and it is a new manufacturer, set the current shop
        if not settings.SHUUP_ENABLE_MULTIPLE_SHOPS or "shops" not in self.fields:
            instance.shops.add(get_shop(self.request))

        return instance


class ManufacturerEditView(CreateOrUpdateView):
    model = Manufacturer
    form_class = ManufacturerForm
    template_name = "shuup/admin/manufacturers/edit.jinja"
    context_object_name = "manufacturer"

    def get_queryset(self):
        return Manufacturer.objects.filter(Q(shops=get_shop(self.request)) | Q(shops__isnull=True))

    def get_form_kwargs(self):
        kwargs = super(ManufacturerEditView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs
