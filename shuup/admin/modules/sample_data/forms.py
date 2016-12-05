# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup.admin.modules.sample_data import manager as sample_manager
from shuup.admin.modules.sample_data.data import BUSINESS_SEGMENTS, CMS_PAGES


class SampleObjectsWizardForm(forms.Form):
    BUSINESS_SEGMENT_CHOICES = sorted([(k, v["name"]) for k, v in BUSINESS_SEGMENTS.items()])

    business_segment = forms.ChoiceField(label=_("Business Segment"),
                                         required=True,
                                         choices=BUSINESS_SEGMENT_CHOICES,
                                         initial="default",
                                         help_text=_("Select your business segment "
                                                     "to install categories."))

    categories = forms.BooleanField(label=_("Install Categories"),
                                    initial=False,
                                    required=False,
                                    help_text=_("Check this to install sample categories."))

    products = forms.BooleanField(label=_("Install Products"),
                                  initial=False,
                                  required=False,
                                  help_text=_("Check this to install sample products."))

    def __init__(self, **kwargs):
        super(SampleObjectsWizardForm, self).__init__(**kwargs)

        # no really choices to make - change to a hidden field widget
        if not len(BUSINESS_SEGMENTS) > 1:
            self.fields["business_segment"].widget = forms.HiddenInput()

        # add the carousel option if its module is installed
        if 'shuup.front.apps.carousel' in settings.INSTALLED_APPS:
            self.fields["carousel"] = forms.BooleanField(
                label=_("Install Carousel"),
                initial=False,
                required=False,
                help_text=_("Check this to install a sample carousel.")
            )

        # add the cms field if the module is installed
        if 'shuup.simple_cms' in settings.INSTALLED_APPS:
            cms_pages_choices = sorted([(k, v["title"]) for k, v in CMS_PAGES.items()])
            self.fields["cms"] = forms.MultipleChoiceField(
                label=_("Install CMS Pages"),
                required=False,
                choices=cms_pages_choices,
                help_text=_("Select the CMS pages you want to install.")
            )


class ConsolidateObjectsForm(forms.Form):

    def __init__(self, **kwargs):
        shop = kwargs.pop("shop")
        super(ConsolidateObjectsForm, self).__init__(**kwargs)

        if sample_manager.get_installed_categories(shop):
            self.fields["categories"] = forms.BooleanField(label=_("Uninstall Categories"),
                                                           initial=False,
                                                           required=False)

        if sample_manager.get_installed_products(shop):
            self.fields["products"] = forms.BooleanField(label=_("Uninstall Products"),
                                                         initial=False,
                                                         required=False)

        if sample_manager.get_installed_carousel(shop):
            self.fields["carousel"] = forms.BooleanField(
                label=_("Uninstall Carousel"),
                initial=False,
                required=False
            )

        if sample_manager.get_installed_cms_pages(shop):
            self.fields["cms"] = forms.BooleanField(label=_("Uninstall CMS Pages"),
                                                    initial=False,
                                                    required=False)
