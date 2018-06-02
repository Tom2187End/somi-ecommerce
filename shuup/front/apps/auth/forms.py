# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from shuup.core.models import get_person_contact
from shuup.utils.djangoenv import has_installed


class EmailAuthenticationForm(AuthenticationForm):

    error_messages = {
        'invalid_login': _("Please enter a correct %(username)s and password. "
                           "Note that both fields may be case-sensitive. "
                           "In case of multiple accounts with same email only username can be used to login."),
        'inactive': _("This account is inactive."),
    }

    def __init__(self, *args, **kwargs):
        super(EmailAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = _("Username or email address")

        if has_installed("shuup.gdpr"):
            from shuup.gdpr.models import GDPRSettings
            if GDPRSettings.get_for_shop(self.request.shop).enabled:
                from shuup.simple_cms.models import Page, PageType
                for page in Page.objects.visible(self.request.shop).filter(page_type=PageType.GDPR_CONSENT_DOCUMENT):
                    self.fields["accept_{}".format(page.id)] = forms.BooleanField(
                        label=_("I have read and accept the {}").format(page.title),
                        help_text=_("Read the <a href='{}' target='_blank'>{}</a>.").format(
                            reverse("shuup:cms_page", kwargs=dict(url=page.url)),
                            page.title
                        ),
                        error_messages=dict(required=_("You must accept to this to authenticate."))
                    )

    def clean_username(self):
        username = self.cleaned_data['username']
        user_model = get_user_model()

        # Note: Always search by username AND by email prevent timing attacks
        try:
            user_by_name = user_model._default_manager.get_by_natural_key(username)
        except ObjectDoesNotExist:
            user_by_name = None

        try:
            user_by_email = user_model._default_manager.get(email=username)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            user_by_email = None

        if not user_by_name and user_by_email:
            return getattr(user_by_email, user_model.USERNAME_FIELD)

        return username

    def confirm_login_allowed(self, user):
        """
        Do not let user with inactive person contact to login.
        """
        if not get_person_contact(user).is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )
        if settings.SHUUP_ENABLE_MULTIPLE_SHOPS and settings.SHUUP_MANAGE_CONTACTS_PER_SHOP:
            if not user.is_superuser:
                shop = self.request.shop
                if shop not in user.contact.shops.all():
                    raise forms.ValidationError(_("You are not allowed to login to this shop."))

        super(EmailAuthenticationForm, self).confirm_login_allowed(user)

        # create GDPR consent
        if has_installed("shuup.gdpr"):
            from shuup.gdpr.utils import create_user_consent_for_all_documents
            create_user_consent_for_all_documents(self.request.shop, user)
