# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.forms import BaseFormSet
from django.http import HttpResponseRedirect
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, UpdateView

from shuup.admin.modules.settings import ViewSettings
from shuup.admin.toolbar import (
    get_default_edit_toolbar, NewActionButton, SettingsActionButton, Toolbar
)
from shuup.admin.utils.forms import add_form_errors_as_messages
from shuup.admin.utils.picotable import PicotableViewMixin
from shuup.admin.utils.urls import (
    get_model_front_url, get_model_url, NoModelUrl
)
from shuup.utils.excs import Problem
from shuup.utils.form_group import FormGroup
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class CreateOrUpdateView(UpdateView):
    add_form_errors_as_messages = False

    def get_object(self, queryset=None):
        if not self.kwargs.get(self.pk_url_kwarg):
            return self.model()
        return super(CreateOrUpdateView, self).get_object(queryset)

    def get_toolbar(self):
        save_form_id = self.get_save_form_id()
        if save_form_id:
            return get_default_edit_toolbar(self, save_form_id)

    def get_context_data(self, **kwargs):
        context = super(CreateOrUpdateView, self).get_context_data(**kwargs)
        context["is_new"] = (not self.object.pk)
        context["front_url"] = get_model_front_url(self.request, self.object)
        context["title"] = get_create_or_change_title(self.request, self.object)
        context["save_form_id"] = self.get_save_form_id()
        context["toolbar"] = self.get_toolbar()
        return context

    def get_save_form_id(self):
        return getattr(self, "save_form_id", None) or "%s_form" % self.get_context_object_name(self.object)

    def get_return_url(self):
        return get_model_url(self.object, kind="list")

    def get_new_url(self):
        return get_model_url(self.object, kind="new")

    def get_success_url(self):
        next = self.request.REQUEST.get("__next")
        try:
            if next == "return":
                return self.get_return_url()
            elif next == "new":
                return self.get_new_url()
        except NoModelUrl:
            pass

        try:
            return super(CreateOrUpdateView, self).get_success_url()
        except ImproperlyConfigured:
            pass

        try:
            return get_model_url(self.object)
        except NoModelUrl:
            pass

    def get_form_kwargs(self):
        kwargs = super(CreateOrUpdateView, self).get_form_kwargs()
        form_class = getattr(self, "form_class", None)
        if form_class and issubclass(form_class, MultiLanguageModelForm):
            kwargs["languages"] = settings.LANGUAGES
        return kwargs

    def form_valid(self, form):
        # This implementation is an amalgamation of
        # * django.views.generic.edit.ModelFormMixin#form_valid
        # * django.views.generic.edit.FormMixin#form_valid
        is_new = (not self.object.pk)
        self.save_form(form)
        add_create_or_change_message(self.request, self.object, is_new=is_new)
        return HttpResponseRedirect(self.get_success_url())

    def save_form(self, form):
        # Subclass hook.
        self.object = form.save()

    def form_invalid(self, form):
        if self.add_form_errors_as_messages:
            # If form is a form group, add form part errors individually
            if isinstance(form, FormGroup):
                for form_part in form.forms.values():
                    # If child form is a formset, add errors for each form in formset
                    if isinstance(form_part, BaseFormSet):
                        for formset_form in form_part:
                            add_form_errors_as_messages(self.request, formset_form)
                    elif form_part.errors:
                        add_form_errors_as_messages(self.request, form_part)
            else:
                add_form_errors_as_messages(self.request, form)
        return super(CreateOrUpdateView, self).form_invalid(form)


def add_create_or_change_message(request, instance, is_new):
    if is_new:
        messages.success(request, _(u"New %s created.") % instance._meta.verbose_name)
    else:
        messages.success(request, _(u"%s edited.") % instance._meta.verbose_name.title())


def get_create_or_change_title(request, instance, name_field=None):
    """
    Get a title suitable for an create-or-update view.

    :param request: Request
    :type request: HttpRequest
    :param instance: Model instance
    :type instance: django.db.models.Model
    :param name_field: Which property to try to read the name from. If None, use `str`
    :type name_field: str
    :return: Title
    :rtype: str
    """
    if not instance.pk:
        return _("New %s") % instance._meta.verbose_name

    if name_field:
        name = getattr(instance, name_field, None)
    else:
        name = "%s" % instance

    if name:
        return force_text(name)

    return _("Unnamed %s") % instance._meta.verbose_name


def check_and_raise_if_only_one_allowed(setting_name, obj):
    if getattr(settings, setting_name, True):
        return
    if not obj.pk and obj.__class__.objects.count() >= 1:
        raise Problem(_("Only one %(model)s permitted.") % {"model": obj._meta.verbose_name})


class PicotableListView(PicotableViewMixin, ListView):

    def __init__(self):
        super(PicotableListView, self).__init__()
        self.settings = ViewSettings(self.model, self.default_columns)
        self.columns = self.settings.columns

    def get_toolbar(self):
        buttons = []
        model = self.model
        if hasattr(self, "get_model"):
            model = self.get_model()
        new_button = NewActionButton.for_model(model)
        if new_button:
            buttons.append(new_button)

        return_url = self.url_identifier if self.url_identifier else None
        settings_button = SettingsActionButton.for_model(model, return_url=return_url)
        if settings_button:
            buttons.append(settings_button)

        return Toolbar(buttons)

    def get_context_data(self, **kwargs):
        context = super(PicotableListView, self).get_context_data(**kwargs)
        context["toolbar"] = self.get_toolbar()
        return context

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
        ]
