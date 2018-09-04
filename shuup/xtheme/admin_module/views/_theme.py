# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import URLActionButton
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.admin.views.wizard import TemplatedWizardFormDef, WizardPane
from shuup.core import cache
from shuup.utils.importing import cached_load
from shuup.xtheme._theme import (
    get_theme_by_identifier, get_theme_cache_key, set_current_theme
)
from shuup.xtheme.models import ThemeSettings


class ActivationForm(forms.Form):
    """
    A very simple form for activating a theme.
    """
    activate = forms.CharField(label=_("activate"))
    selected_style = forms.CharField(required=False, widget=forms.HiddenInput())


class ThemeWizardPane(WizardPane):
    identifier = "theme"
    icon = "xtheme/theme.png"
    title = _("Theme")
    text = _("Choose a theme for your shop")

    def visible(self):
        return (ThemeSettings.objects.filter(active=False, shop=self.object).count() == 0)

    def get_form_defs(self):
        shop = self.object
        context = cached_load("SHUUP_XTHEME_ADMIN_THEME_CONTEXT")(shop)
        context.update({"shop": shop})

        current_theme_class = (context["current_theme"] or context["theme_classes"][0])
        current_theme_settings = ThemeSettings.objects.get_or_create(
            shop=shop,
            theme_identifier=current_theme_class.identifier
        )[0]
        context["active_stylesheet"] = current_theme_settings.data.get("settings", {}).get("stylesheet", None)

        return [
            TemplatedWizardFormDef(
                template_name="shuup/xtheme/admin/wizard.jinja",
                name="theme",
                form_class=ActivationForm,
                context=context
            )
        ]

    def form_valid(self, form):
        identifier = form["theme"].cleaned_data["activate"]
        data = {
            "settings": {
               "stylesheet": form["theme"].cleaned_data["selected_style"]
            }
        }
        theme_settings, created = ThemeSettings.objects.get_or_create(
            theme_identifier=identifier,
            shop=get_shop(self.request)
        )
        if created:
            theme_settings.data = data
            theme_settings.save()
        else:
            theme_settings.update_settings(data["settings"])

        set_current_theme(identifier, self.object)
        cache.bump_version(get_theme_cache_key(get_shop(self.request)))


class ThemeConfigView(FormView):
    """
    A view for listing and activating themes.
    """
    template_name = "shuup/xtheme/admin/config.jinja"
    form_class = ActivationForm

    def get_context_data(self, **kwargs):
        context = super(ThemeConfigView, self).get_context_data(**kwargs)
        shop = get_shop(self.request)
        context.update(cached_load("SHUUP_XTHEME_ADMIN_THEME_CONTEXT")(shop))
        return context

    def form_valid(self, form):
        identifier = form.cleaned_data["activate"]
        set_current_theme(identifier, get_shop(self.request))
        messages.success(self.request, _("Theme activated."))
        return HttpResponseRedirect(self.request.path)


class ThemeConfigDetailView(CreateOrUpdateView):
    """
    A view for configuring a single theme.
    """
    model = ThemeSettings
    template_name = "shuup/xtheme/admin/config_detail.jinja"
    form_class = forms.Form
    context_object_name = "theme_settings"
    add_form_errors_as_messages = True

    def get_object(self, queryset=None):
        return ThemeSettings.objects.get_or_create(
            theme_identifier=self.kwargs["theme_identifier"],
            shop=get_shop(self.request)
        )[0]

    def get_theme(self):
        """
        Get the theme object to configure.

        :return: Theme object
        :rtype: shuup.xtheme.Theme
        """
        return get_theme_by_identifier(
            identifier=self.kwargs["theme_identifier"],
            shop=get_shop(self.request)
        )

    def get_context_data(self, **kwargs):
        context = super(ThemeConfigDetailView, self).get_context_data(**kwargs)
        shop = get_shop(self.request)
        context["theme"] = self.get_theme()
        context["active_stylesheet"] = self.object.data.get("settings", {}).get("stylesheet", None)
        context["shop"] = shop
        return context

    def get_form(self, form_class=None):
        return self.get_theme().get_configuration_form(form_kwargs=self.get_form_kwargs())

    def get_success_url(self):
        return reverse("shuup_admin:xtheme.config_detail", kwargs={
            "theme_identifier": self.object.theme_identifier
        })

    def save_form(self, form):
        super(ThemeConfigDetailView, self).save_form(form)
        cache.bump_version(get_theme_cache_key(get_shop(self.request)))

    def get_toolbar(self):
        toolbar = super(ThemeConfigDetailView, self).get_toolbar()
        toolbar.append(
            URLActionButton(
                text=_("Snippet injection"),
                icon="fa fa-magic",
                url=reverse("shuup_admin:xtheme_snippet.list"),
                extra_css_class="btn-info"
            )
        )
        return toolbar


class ThemeGuideTemplateView(TemplateView):
    template_name = None

    def dispatch(self, request, *args, **kwargs):
        theme = get_theme_by_identifier(kwargs["theme_identifier"], shop=get_shop(self.request))
        self.template_name = theme.guide_template
        return super(ThemeGuideTemplateView, self).dispatch(request, *args, **kwargs)
