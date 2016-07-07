# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from collections import Counter

import pytest
from django.core.exceptions import ImproperlyConfigured

from shuup.admin.utils.urls import admin_url, get_model_url, NoModelUrl
from shuup.core.models import Product
from shuup_tests.admin.utils import admin_only_urls
from shuup_tests.utils.faux_users import StaffUser


def test_model_url():
    with admin_only_urls():
        with pytest.raises(NoModelUrl):
            get_model_url(Counter)  # That's silly!
        p = Product()
        p.pk = 3
        assert get_model_url(p)


def test_model_url_with_permissions():
    permissions = set(["shuup.add_product", "shuup.delete_product", "shuup.change_product"])
    p = Product()
    p.pk = 3

    # If no user is given, don't check for permissions
    assert get_model_url(p)

    # If a user is given and no permissions are provided, check for default model permissions
    user = StaffUser()
    with pytest.raises(NoModelUrl):
        assert get_model_url(p, user=user)

    # If a user is given and permissions are provided, check for those permissions
    assert get_model_url(p, user=user, required_permissions=())
    with pytest.raises(NoModelUrl):
        assert get_model_url(p, user=user, required_permissions=["shuup.add_product"])

    # Confirm that url is returned with correct permissions
    user.permissions = permissions
    assert get_model_url(p, user=user)
    assert get_model_url(p, user=user, required_permissions=permissions)


def test_invalid_admin_url():
    with pytest.raises(ImproperlyConfigured):
        admin_url("", "")


def test_admin_url_prefix():
    assert admin_url("", "foo", prefix="bar")._callback_str == "bar.foo"
