# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import resolve_url
from shuup.core.models import (
    CompanyContact, get_company_contact, get_person_contact
)
from shuup.testing.factories import get_default_shop
from shuup.testing.soup_utils import extract_form_fields
from shuup_tests.utils import SmartClient
from shuup_tests.utils.fixtures import (
    regular_user, REGULAR_USER_PASSWORD, REGULAR_USER_USERNAME
)


def default_customer_data():
    return {
        "contact-first_name": "Captain",
        "contact-last_name": "Shuup",
        "contact-email": "captain@shuup.local",
        "contact-gender": "o",
    }


def default_company_data():
    return {
        "contact-name": "Fakerr",
        "contact-tax_number": "111110",
        "contact-phone": "11-111-111-1110",
        "contact-email": "captain@shuup.local",
    }


def default_address_data(address_type):
    return {
        "{}-name".format(address_type) : "Fakerr",
        "{}-phone".format(address_type): "11-111-111-1110",
        "{}-email".format(address_type): "captain@shuup.local",
        "{}-street".format(address_type): "123 Fake St.",
        "{}-postal_code".format(address_type): "1234567",
        "{}-city".format(address_type): "Shuupville",
        "{}-country".format(address_type): "US",
    }


@pytest.mark.django_db
def test_new_user_information_edit():
    client = SmartClient()
    get_default_shop()
    # create new user
    user_password = "niilo"
    user = get_user_model().objects.create_user(
        username="Niilo_Nyyppa",
        email="niilo@example.shuup.com",
        password=user_password,
        first_name="Niilo",
        last_name="Nyyppä",
    )

    client.login(username=user.username, password=user_password)

    # make sure all information matches in form
    customer_edit_url = reverse("shuup:customer_edit")
    soup = client.soup(customer_edit_url)

    assert soup.find(attrs={"name": "contact-email"})["value"] == user.email
    assert soup.find(attrs={"name": "contact-first_name"})["value"] == user.first_name
    assert soup.find(attrs={"name": "contact-last_name"})["value"] == user.last_name

    # Test POSTing
    form = extract_form_fields(soup)
    new_email = "nyyppa@example.shuup.com"
    form["contact-email"] = new_email
    form["contact-country"] = "FI"

    for prefix in ("billing", "shipping"):
        form["%s-city" % prefix] = "test-city"
        form["%s-email" % prefix] = new_email
        form["%s-street" % prefix] = "test-street"
        form["%s-country" % prefix] = "FI"

    response, soup = client.response_and_soup(customer_edit_url, form, "post")

    assert response.status_code == 302
    assert get_user_model().objects.get(pk=user.pk).email == new_email


@pytest.mark.django_db
def test_customer_edit_redirects_to_login_if_not_logged_in():
    get_default_shop()  # Front middleware needs a Shop to exists
    urls = ["shuup:customer_edit", "shuup:company_edit"]
    for url in urls:
        response = SmartClient().get(reverse(url), follow=False)
        assert response.status_code == 302  # Redirection ("Found")
        assert resolve_url(settings.LOGIN_URL) in response.url


@pytest.mark.django_db
def test_company_edit_form_links_company(regular_user, rf):
    get_default_shop()
    person = get_person_contact(regular_user)
    assert not get_company_contact(regular_user)

    client = SmartClient()
    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
    company_edit_url = reverse("shuup:company_edit")
    soup = client.soup(company_edit_url)

    data = default_company_data()
    data.update(default_address_data("billing"))
    data.update(default_address_data("shipping"))

    response, soup = client.response_and_soup(company_edit_url, data, "post")

    assert response.status_code == 302
    assert get_company_contact(regular_user)


@pytest.mark.django_db
def test_company_still_linked_if_customer_contact_edited(regular_user):
    get_default_shop()
    person = get_person_contact(regular_user)
    assert not get_company_contact(regular_user)

    company = CompanyContact()
    company.save()
    company.members.add(person)
    assert get_company_contact(regular_user)

    client = SmartClient()
    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
    customer_edit_url = reverse("shuup:customer_edit")
    soup = client.soup(customer_edit_url)

    data = default_customer_data()
    data.update(default_address_data("billing"))
    data.update(default_address_data("shipping"))

    response, soup = client.response_and_soup(customer_edit_url, data, "post")

    assert response.status_code == 302
    assert get_company_contact(regular_user)


@pytest.mark.django_db
@pytest.mark.parametrize("password_value,new_password_2,expected", [
    (REGULAR_USER_PASSWORD, "12345", True),
    ("some_other_password", "12345", False),
    (REGULAR_USER_PASSWORD, "12345678", False),
])
def test_user_change_password(regular_user, password_value, new_password_2, expected):
    get_default_shop()
    assert check_password(REGULAR_USER_PASSWORD, regular_user.password)

    client = SmartClient()
    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
    change_password_url = reverse("shuup:change_password")

    new_password = "12345"
    data = {
        "old_password": password_value,
        "new_password1": new_password,
        "new_password2": new_password_2,
    }

    response, soup = client.response_and_soup(change_password_url, data, "post")
    user = get_user_model().objects.get(pk=regular_user.pk)
    assert regular_user == user

    assert check_password(REGULAR_USER_PASSWORD, user.password) != expected
    assert check_password(new_password, user.password) == expected


@pytest.mark.django_db
def test_company_tax_number_limitations(regular_user):
    get_default_shop()
    person = get_person_contact(regular_user)
    assert not get_company_contact(regular_user)

    client = SmartClient()
    client.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)
    company_edit_url = reverse("shuup:company_edit")
    soup = client.soup(company_edit_url)

    data = default_company_data()
    data.update(default_address_data("billing"))
    data.update(default_address_data("shipping"))

    response, soup = client.response_and_soup(company_edit_url, data, "post")

    assert response.status_code == 302
    assert get_company_contact(regular_user)

    # re-save should work properly
    response, soup = client.response_and_soup(company_edit_url, data, "post")
    assert response.status_code == 302
    client.logout()

    # another company tries to use same tax number
    new_user_password = "derpy"
    new_user_username = "derpy"
    user = User.objects.create_user(new_user_username, "derpy@shuup.com", new_user_password)
    person = get_person_contact(user=user)
    assert not get_company_contact(user)

    client = SmartClient()
    client.login(username=new_user_username, password=new_user_password)
    company_edit_url = reverse("shuup:company_edit")
    soup = client.soup(company_edit_url)

    data = default_company_data()
    data.update(default_address_data("billing"))
    data.update(default_address_data("shipping"))

    response, soup = client.response_and_soup(company_edit_url, data, "post")
    assert response.status_code == 200  # this time around, nothing was saved.
    assert not get_company_contact(user)  # company contact yet

    # change tax number
    data["contact-tax_number"] = "111111"
    response, soup = client.response_and_soup(company_edit_url, data, "post")
    assert response.status_code == 302  # this time around, nothing was saved.
    assert get_company_contact(user)  # company contact yet

    # go back to normal and try to get tax number approved
    data["contact-tax_number"] = "111110"
    response, soup = client.response_and_soup(company_edit_url, data, "post")
    assert response.status_code == 200  # this time around, nothing was saved.
