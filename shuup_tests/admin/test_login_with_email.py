# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from django.contrib.auth import (
    get_user, get_user_model, REDIRECT_FIELD_NAME
)
from django.core.urlresolvers import reverse

from shuup.testing.factories import get_default_shop
from shuup_tests.utils.fixtures import regular_user, REGULAR_USER_PASSWORD

regular_user = regular_user  # noqa


def prepare_user(user):
    user.is_active = True
    user.set_password(REGULAR_USER_PASSWORD)
    user.save(update_fields=("is_active", "password"))


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_with_email_1(client, regular_user, rf):
    get_default_shop()
    prepare_user(regular_user)
    redirect_target = "/redirect-success/"
    response = client.post(reverse("shuup_admin:login"), data={
        "username": regular_user.email,
        "password": REGULAR_USER_PASSWORD,
        REDIRECT_FIELD_NAME: redirect_target
    })

    assert response.get("location")
    assert response.get("location").endswith(redirect_target)

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == regular_user, "User is logged in"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_with_email_2(client, regular_user, rf):
    # Create user with same email as regular user to fail login
    get_user_model().objects.create_user(
        username="el_person",
        password="123123",
        email=regular_user.email
    )

    get_default_shop()
    prepare_user(regular_user)
    redirect_target = "/redirect-success/"
    client.post(reverse("shuup_admin:login"), data={
        "username": regular_user.email,
        "password": REGULAR_USER_PASSWORD,
        REDIRECT_FIELD_NAME: redirect_target
    })

    request = rf.get("/")
    request.session = client.session
    assert get_user(request).is_anonymous(), "User is still anonymous"

    # Login with unknown email
    client.post(reverse("shuup_admin:login"), data={
        "username": "unknown@example.com",
        "password": REGULAR_USER_PASSWORD,
        REDIRECT_FIELD_NAME: redirect_target
    })

    request = rf.get("/")
    request.session = client.session
    assert get_user(request).is_anonymous(), "User is still anonymous"

    # Login with username should work normally
    response = client.post(reverse("shuup_admin:login"), data={
        "username": regular_user.username,
        "password": REGULAR_USER_PASSWORD,
        REDIRECT_FIELD_NAME: redirect_target
    })

    assert response.get("location")
    assert response.get("location").endswith(redirect_target)

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == regular_user, "User is logged in"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_with_email_3(client, regular_user, rf):
    new_user_password = "123123"
    new_user = get_user_model().objects.create_user(
        username=regular_user.email,
        password=new_user_password,
        email=regular_user.email
    )

    get_default_shop()
    prepare_user(regular_user)
    redirect_target = "/redirect-success/"

    # Login with new_user username should work even if there is users with same email
    response = client.post(reverse("shuup_admin:login"), data={
        "username": regular_user.email,
        "password": new_user_password,
        REDIRECT_FIELD_NAME: redirect_target
    })

    assert response.get("location")
    assert response.get("location").endswith(redirect_target)

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == new_user, "User is logged in"
