# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import re
import uuid

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from shuup import configuration
from shuup.admin.modules.contacts.views import ContactDetailView
from shuup.core.models import CompanyContact
from shuup.core.models import PersonContact
from shuup.front.apps.customer_information.views import CompanyEditView
from shuup.notify.models import Script
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware

username = "u-%d" % uuid.uuid4().time
email = "%s@shuup.local" % username


@pytest.mark.django_db
@pytest.mark.parametrize("requiring_activation", (False, True))
def test_registration(django_user_model, client, requiring_activation):
    if "shuup.front.apps.registration" not in settings.INSTALLED_APPS:
        pytest.skip("shuup.front.apps.registration required in installed apps")

    get_default_shop()

    with override_settings(
        SHUUP_REGISTRATION_REQUIRES_ACTIVATION=requiring_activation,
    ):
        client.post(reverse("shuup:registration_register"), data={
            "username": username,
            "email": email,
            "password1": "password",
            "password2": "password",
        })
        user = django_user_model.objects.get(username=username)
        if requiring_activation:
            assert not user.is_active
        else:
            assert user.is_active

@pytest.mark.django_db
@pytest.mark.parametrize("requiring_activation", (False, True))
def test_registration_2(django_user_model, client, requiring_activation):
    if "shuup.front.apps.registration" not in settings.INSTALLED_APPS:
        pytest.skip("shuup.front.apps.registration required in installed apps")

    get_default_shop()

    with override_settings(
        SHUUP_REGISTRATION_REQUIRES_ACTIVATION=requiring_activation,
    ):
        response = client.post(reverse("shuup:registration_register"), data={
            "username": username,
            "email": email,
            "password1": "password",
            "password2": "password",
            "next": reverse('shuup:checkout')
        })
        user = django_user_model.objects.get(username=username)
        assert response.status_code == 302 #redirect
        assert response.url.endswith(reverse('shuup:checkout'))


def test_settings_has_account_activation_days():
    assert hasattr(settings, 'ACCOUNT_ACTIVATION_DAYS')


@pytest.mark.django_db
def test_password_recovery_user_receives_email_1(client):
    get_default_shop()
    user = get_user_model().objects.create_user(
        username="random_person",
        password="asdfg",
        email="random@shuup.local"
    )
    n_outbox_pre = len(mail.outbox)
    client.post(
        reverse("shuup:recover_password"),
        data={
            "email": user.email
        }
    )
    assert (len(mail.outbox) == n_outbox_pre + 1), "Sending recovery email has failed"
    assert 'http' in mail.outbox[-1].body, "No recovery url in email"
    # ticket #SHUUP-606
    assert 'site_name' not in mail.outbox[-1].body, "site_name variable has no content"


@pytest.mark.django_db
def test_password_recovery_user_receives_email_2(client):
    get_default_shop()
    user = get_user_model().objects.create_user(
        username="random_person",
        password="asdfg",
        email="random@shuup.local"
    )
    n_outbox_pre = len(mail.outbox)
    # Recover with username
    client.post(
        reverse("shuup:recover_password"),
        data={
            "username": user.username
        }
    )
    assert (len(mail.outbox) == n_outbox_pre + 1), "Sending recovery email has failed"
    assert 'http' in mail.outbox[-1].body, "No recovery url in email"
    assert 'site_name' not in mail.outbox[-1].body, "site_name variable has no content"


@pytest.mark.django_db
def test_password_recovery_user_receives_email_3(client):
    get_default_shop()
    user = get_user_model().objects.create_user(
        username="random_person",
        password="asdfg",
        email="random@shuup.local"
    )
    get_user_model().objects.create_user(
        username="another_random_person",
        password="asdfg",
        email="random@shuup.local"
    )

    n_outbox_pre = len(mail.outbox)
    # Recover all users with email random@shuup.local
    client.post(
        reverse("shuup:recover_password"),
        data={
            "email": user.email
        }
    )
    assert (len(mail.outbox) == n_outbox_pre + 2), "Sending 2 recovery emails has failed"
    assert 'http' in mail.outbox[-1].body, "No recovery url in email"
    assert 'site_name' not in mail.outbox[-1].body, "site_name variable has no content"


@pytest.mark.django_db
def test_password_recovery_user_with_no_email(client):
    get_default_shop()
    user = get_user_model().objects.create_user(
        username="random_person",
        password="asdfg"
    )
    n_outbox_pre = len(mail.outbox)
    client.post(
        reverse("shuup:recover_password"),
        data={
            "username": user.username
        }
    )
    assert (len(mail.outbox) == n_outbox_pre), "No recovery emails sent"


@pytest.mark.django_db
@pytest.mark.parametrize("requiring_activation", (False, True))
def test_user_will_be_redirected_to_user_account_page_after_activation(client, requiring_activation):
    """
    1. Register user
    2. Dig out the urls from the email
    3. Get the url and see where it redirects
    4. See that user's email is in content (in input)
    5. Check that the url poins to user_account-page
    """
    if "shuup.front.apps.registration" not in settings.INSTALLED_APPS:
        pytest.skip("shuup.front.apps.registration required in installed apps")
    if "shuup.front.apps.customer_information" not in settings.INSTALLED_APPS:
        pytest.skip("shuup.front.apps.customer_information required in installed apps")

    shop = get_default_shop()
    Script.objects.create(
        event_identifier="registration_received",
        name="Send User Activation URL Email",
        enabled=True,
        shop=shop,
        template="registration_received_email",
        _step_data=[
            {
                'conditions': [
                    {
                        "template_data": {},
                        "v1": {"variable": "user_is_active"},
                        "identifier": "boolean_equal",
                        "v2": {"constant": False}
                    }
                ],
                'next': 'stop',
                'cond_op': 'all',
                'actions': [
                    {
                        'fallback_language': {'constant': 'en'},
                        'template_data': {
                            'pt-br': {'content_type': 'html', 'subject': '', 'body': ''},
                            'en': {
                                'content_type': 'html',
                                'subject': 'User Activation Link',
                                'body': '{{activation_url}}'
                            },
                        },
                        'recipient': {'variable': 'customer_email'},
                        'language': {'variable': 'language'},
                        'identifier': 'send_email'
                    },
                ],
                'enabled': True
            }
        ],
    )
    with override_settings(
        SHUUP_REGISTRATION_REQUIRES_ACTIVATION=requiring_activation,
    ):
        response = client.post(reverse("shuup:registration_register"), data={
            "username": username,
            "email": email,
            "password1": "password",
            "password2": "password",
        }, follow=True)
        user = get_user_model().objects.get(username=username)

        if requiring_activation:
            body = mail.outbox[-1].body
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', body)
            assert user.registrationprofile.activation_key in urls[0]
            response = client.get(urls[0], follow=True)
            assert email.encode('utf-8') in response.content, 'email should be found from the page.'
            assert reverse('shuup:customer_edit') == response.request['PATH_INFO'], 'user should be on the account-page.'
        else:
            assert len(mail.outbox) == 0
            assert user.is_active
            assert reverse('shuup:index') == response.request['PATH_INFO']


@pytest.mark.django_db
@pytest.mark.parametrize("allow_company_registration", (False, True))
@pytest.mark.parametrize("company_registration_requires_approval", (False, True))
def test_company_registration(django_user_model, client, allow_company_registration,
                              company_registration_requires_approval, rf, admin_user):
    if "shuup.front.apps.registration" not in settings.INSTALLED_APPS:
        pytest.skip("shuup.front.apps.registration required in installed apps")

    shop = get_default_shop()

    configuration.set(None, "allow_company_registration", allow_company_registration)
    configuration.set(None, "company_registration_requires_approval", company_registration_requires_approval)

    url = reverse("shuup:registration_register_company")
    Script.objects.create(
        event_identifier="company_approved_by_admin",
        name="Send Company Activated Email",
        enabled=True,
        shop=shop,
        template="company_activated_email",
        _step_data=[
            {'actions': [
                {
                    'fallback_language': {'constant': 'en'},
                    'template_data': {
                        'en': {
                            'content_type': 'html',
                            'subject': 'Company activated',
                            'body': 'Company has been approved. '
                                    'Please activate your account by clicking the link: {{activation_url}}'
                        },
                    },
                    'recipient': {'variable': 'customer_email'},
                    'language': {'variable': 'language'},
                    'identifier': 'send_email'}
            ],
                'enabled': True,
                'next': 'stop',
                'conditions': [],
                'cond_op': 'all'
            }
        ]
    )
    Script.objects.create(
        event_identifier="company_registration_received",
        name="Send Company Registration Received Email",
        enabled=True,
        shop=shop,
        template="company_registration_received_email",
        _step_data=[
            {
                'conditions': [],
                'next': 'stop',
                'cond_op': 'all',
                'actions': [
                    {
                        'fallback_language': {'constant': 'en'},
                        'template_data': {
                             'en': {
                                 'content_type': 'html',
                                 'subject': 'Generic welcome message',
                                 'body': 'Welcome!'
                             },
                        },
                        'recipient': {'variable': 'customer_email'},
                        'language': {'variable': 'language'},
                        'identifier': 'send_email'
                    },
                    {
                        'fallback_language': {'constant': 'en'},
                        'template_data': {
                            'en': {
                                'content_type': 'plain',
                                'subject': 'New company registered',
                                'body': 'New company registered'
                            },
                        },
                        'recipient': {'constant': 'admin@host.local'},
                        'language': {'constant': 'en'},
                        'identifier': 'send_email'
                    }
                ],
                'enabled': True}],
    )
    if not allow_company_registration:
        response = client.get(url)
        assert response.status_code == 404
    else:
        response = client.post(url, data={
            'company-name': "Test company",
            'company-name_ext': "test",
            'company-tax_number': "12345",
            'company-email': "test@example.com",
            'company-phone': "123123",
            'company-www': "",
            'billing-street': "testa tesat",
            'billing-street2': "",
            'billing-postal_code': "12345",
            'billing-city': "test test",
            'billing-region': "",
            'billing-region_code': "",
            'billing-country': "FI",
            'contact_person-first_name': "Test",
            'contact_person-last_name': "Tester",
            'contact_person-email': email,
            'contact_person-phone': "123",
            'user_account-username': username,
            'user_account-password1': "password",
            'user_account-password2': "password",
        })

        user = django_user_model.objects.get(username=username)
        contact = PersonContact.objects.get(user=user)
        company = CompanyContact.objects.get(members__in=[contact])

        # one of each got created
        assert django_user_model.objects.count() == 2  # admin_user + registered user
        assert PersonContact.objects.count() == 1
        assert CompanyContact.objects.count() == 1
        # and they are innactive
        if company_registration_requires_approval:
            assert PersonContact.objects.filter(is_active=False).count() == 1
            assert CompanyContact.objects.filter(is_active=False).count() == 1
            assert mail.outbox[0].subject == "Generic welcome message"
            assert mail.outbox[1].subject == "New company registered"
            # Activating Company for the first time from admin triggers company_approved_by_admin event
            request = apply_request_middleware(rf.post("/", {"set_is_active": "1"}), user=admin_user)
            view_func = ContactDetailView.as_view()
            response = view_func(request, pk=company.pk)
            urls = re.findall(
                'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                mail.outbox[2].body)
            assert mail.outbox[2].subject == "Company activated"
            assert user.registrationprofile.activation_key in urls[0]
            # User receives link to activate his own account
            response = client.get(urls[0], follow=True)
            user.refresh_from_db()
            assert user.is_active is True
        else:
            assert PersonContact.objects.filter(is_active=True).count() == 1
            assert CompanyContact.objects.filter(is_active=True).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("allow_company_registration", (False, True))
@pytest.mark.parametrize("company_registration_requires_approval", (False, True))
def test_create_company_from_customer_dashboard(allow_company_registration, company_registration_requires_approval,
                                                client, rf, admin_user):
    if "shuup.front.apps.registration" not in settings.INSTALLED_APPS:
        pytest.skip("shuup.front.apps.registration required in installed apps")

    shop = get_default_shop()
    configuration.set(None, "allow_company_registration", allow_company_registration)
    configuration.set(None, "company_registration_requires_approval", company_registration_requires_approval)

    Script.objects.create(
        event_identifier="company_registration_received",
        name="Send Company Registration Received Email",
        enabled=True,
        shop=shop,
        template="company_registration_received_email",
        _step_data=[
            {
                'conditions': [],
                'next': 'stop',
                'cond_op': 'all',
                'actions': [
                    {
                        'fallback_language': {'constant': 'en'},
                        'template_data': {
                             'en': {
                                 'content_type': 'html',
                                 'subject': 'Company Registered',
                                 'body': 'Waiting approval'
                             },
                        },
                        'recipient': {'variable': 'customer_email'},
                        'language': {'variable': 'language'},
                        'identifier': 'send_email'
                    },
                ],
                'enabled': True}],
    )
    Script.objects.create(
        event_identifier="company_approved_by_admin",
        name="Send Company Activated Email",
        enabled=True,
        shop=shop,
        template="company_activated_email",
        _step_data=[
            {'actions': [
                {
                    'fallback_language': {'constant': 'en'},
                    'template_data': {
                        'en': {
                            'content_type': 'html',
                            'subject': 'Company activated',
                            'body': 'Company has been approved. '
                                    'Please activate your account by clicking the link: {{activation_url}}'
                        },
                    },
                    'recipient': {'variable': 'customer_email'},
                    'language': {'variable': 'language'},
                    'identifier': 'send_email'}
            ],
                'enabled': True,
                'next': 'stop',
                'conditions': [],
                'cond_op': 'all'
            }
        ]
    )
    # This view creates CompanyContact object for already registered user
    view_func = CompanyEditView.as_view()

    if not allow_company_registration:
        # If company registration is not allowed,
        # can't create company contacts from customer dashboard
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        response = view_func(request)
        assert response.status_code == 404
    else:
        request = apply_request_middleware(
            rf.post("/", {
                'contact-name': "Test company",
                'contact-name_ext': "test",
                'contact-tax_number': "12345",
                'contact-email': "test@example.com",
                'contact-phone': "123123",
                'contact-www': "",
                'billing-name': "testa tesat",
                'billing-phone': "testa tesat",
                'billing-email': email,
                'billing-street': "testa tesat",
                'billing-street2': "",
                'billing-postal_code': "12345",
                'billing-city': "test test",
                'billing-region': "",
                'billing-region_code': "",
                'billing-country': "FI",
                'shipping-name': "testa tesat",
                'shipping-phone': "testa tesat",
                'shipping-email': email,
                'shipping-street': "testa tesat",
                'shipping-street2': "",
                'shipping-postal_code': "12345",
                'shipping-city': "test test",
                'shipping-region': "",
                'shipping-region_code': "",
                'shipping-country': "FI",
            }), user=admin_user)
        response = view_func(request)
        if company_registration_requires_approval:
            # CompanyContact was created as inactive but PersonContact stays active
            assert CompanyContact.objects.filter(is_active=False).count() == 1
            assert PersonContact.objects.filter(is_active=True).count() == 1
            assert mail.outbox[0].subject == "Company Registered"
            # Activate new CompanyContact from admin
            request = apply_request_middleware(rf.post("/", {"set_is_active": "1"}), user=admin_user)
            view_func = ContactDetailView.as_view()
            response = view_func(request, pk=CompanyContact.objects.first().pk)
            urls = re.findall(
                'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                mail.outbox[1].body)
            assert mail.outbox[1].subject == "Company activated"
            assert CompanyContact.objects.filter(is_active=True).count() == 1
        else:
            assert CompanyContact.objects.filter(is_active=True).count() == 1
            assert PersonContact.objects.filter(is_active=True).count() == 1
