# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.http import HttpResponseRedirect

from shoop.admin.utils.urls import get_model_url
from shoop.admin.utils.views import add_create_or_change_message
from shoop.apps.provides import get_provide_objects
from shoop.utils.form_group import FormDef, FormGroup


class TemplatedFormDef(FormDef):
    def __init__(self, name, form_class, template_name, required=True, kwargs=None):
        self.template_name = template_name
        super(TemplatedFormDef, self).__init__(
            name=name,
            form_class=form_class,
            required=required,
            kwargs=kwargs
        )


class FormPart(object):
    priority = 0

    def __init__(self, request, object=None):
        self.request = request
        self.object = object

    def get_form_defs(self):
        return ()

    def form_valid(self, form):
        pass


class FormPartsViewMixin(object):
    fields = ()  # Dealt with by the FormGroup
    request = None
    form_part_class_provide_key = None
    base_form_part_classes = ()

    def get_form_class(self):
        return None  # Dealt with by `get_form`; this will just squelch Django warnings

    def get_form_part_classes(self):
        form_part_classes = (
            list(self.base_form_part_classes) +
            list(get_provide_objects(self.form_part_class_provide_key))
        )
        return form_part_classes

    def get_form_parts(self, object):
        form_part_classes = self.get_form_part_classes()
        form_parts = [form_part_class(request=self.request, object=object) for form_part_class in form_part_classes]
        form_parts.sort(key=lambda form_part: getattr(form_part, "priority", 0))
        return form_parts

    def get_form(self, form_class=None):
        kwargs = self.get_form_kwargs()
        instance = kwargs.pop("instance", None)
        if not instance.pk:
            kwargs["initial"] = dict(self.request.GET.items())
        fg = FormGroup(**kwargs)
        form_parts = self.get_form_parts(instance)
        for form_part in form_parts:
            for form_def in form_part.get_form_defs():
                fg.form_defs[form_def.name] = form_def
        fg.instantiate_forms()
        return fg


class SaveFormPartsMixin(object):
    request = None  # Placate "missing field" errors
    object = None  # --"--

    def save_form_parts(self, form):
        is_new = (not self.object.pk)
        form_parts = self.get_form_parts(self.object)
        for form_part in form_parts:
            retval = form_part.form_valid(form)

            if retval is not None:  # Allow a form part to change the identity of the object
                self.object = retval
                for form_part in form_parts:
                    form_part.object = self.object

        add_create_or_change_message(self.request, self.object, is_new)

        if hasattr(self, "get_success_url"):
            return HttpResponseRedirect(self.get_success_url())

        if is_new:
            return HttpResponseRedirect(get_model_url(self.object))
        else:
            return HttpResponseRedirect(self.request.path)
