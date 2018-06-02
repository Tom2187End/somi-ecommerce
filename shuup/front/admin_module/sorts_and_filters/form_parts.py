# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.apps.provides import get_provide_objects
from shuup.front.utils.sorts_and_filters import (
    FORM_MODIFIER_PROVIDER_KEY, get_configuration, set_configuration
)


class ConfigurationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ConfigurationForm, self).__init__(*args, **kwargs)
        for extend_class in get_provide_objects(FORM_MODIFIER_PROVIDER_KEY) or []:
            for field_key, field in extend_class().get_admin_fields() or []:
                self.fields[field_key] = field


class ConfigurationShopFormPart(FormPart):
    priority = 7
    name = "product_list_facets"
    form = ConfigurationForm

    def get_form_defs(self):
        if not self.object.pk:
            return
        yield TemplatedFormDef(
            name=self.name,
            form_class=self.form,
            template_name="shuup/front/admin/sorts_and_filters.jinja",
            required=False,
            kwargs={"initial": get_configuration(shop=self.object)})

    def form_valid(self, form):
        if self.name in form.forms:
            set_configuration(shop=self.object, data=form[self.name].cleaned_data)


class ConfigurationCategoryFormPart(FormPart):
    priority = 7
    name = "product_list_facets"
    form = ConfigurationForm

    def get_form_defs(self):
        if not self.object.pk:
            return
        yield TemplatedFormDef(
            name=self.name,
            form_class=self.form,
            template_name="shuup/front/admin/sorts_and_filters.jinja",
            required=False,
            kwargs={"initial": get_configuration(category=self.object)})

    def form_valid(self, form):
        if self.name in form.forms:
            set_configuration(category=self.object, data=form[self.name].cleaned_data)
