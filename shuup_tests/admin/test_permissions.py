# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.admin.menu import get_menu_entry_categories
from shuup.admin.modules.customers_dashboard import CustomersDashboardModule
from shuup.admin.modules.sales_dashboard import SalesDashboardModule
from shuup.admin.module_registry import get_modules, replace_modules
from shuup.admin.toolbar import (
    DropdownActionButton, DropdownItem, JavaScriptActionButton,
    PostActionButton, URLActionButton
)
from shuup.admin.utils.permissions import (
    get_default_model_permissions, get_permission_object_from_string,
    get_permissions_from_urls
)
from shuup.core.models import Product
from shuup_tests.admin.fixtures.test_module import ARestrictedTestModule
from shuup_tests.utils.faux_users import StaffUser


migrated_permissions = {
    CustomersDashboardModule: ("shuup.view_customers_dashboard"),
    SalesDashboardModule: ("shuup.view_sales_dashboard"),
}


def test_default_model_permissions():
    permissions = set(["shuup.add_product", "shuup.delete_product", "shuup.change_product"])

    assert get_default_model_permissions(Product) == permissions


def test_permissions_for_menu_entries(rf, admin_user):
    permissions = set(["shuup.add_product", "shuup.delete_product", "shuup.change_product"])

    request = rf.get("/")
    request.user = StaffUser()
    request.user.permissions = permissions

    with replace_modules([ARestrictedTestModule]):
        modules = [m for m in get_modules()]
        assert request.user.permissions == modules[0].get_required_permissions()

        categories = get_menu_entry_categories(request)
        assert categories

        # Make sure category is displayed if user has correct permissions
        test_category_menu_entries = [cat for cat in categories if cat.name == "RestrictedTest"][0]
        assert any(me.text == "OK" for me in test_category_menu_entries)

        # No menu items should be displayed if user has no permissions
        request.user.permissions = []
        categories = get_menu_entry_categories(request)
        assert not categories


@pytest.mark.django_db
def test_valid_permissions_for_all_modules():
    """
    If a module requires permissions, make sure all url and module-
    level permissions are valid.

    Modules that add permissions using migrations must be checked
    manually since their permissions will not be in the test database.
    """
    for module in get_modules():
        url_permissions = set(get_permissions_from_urls(module.get_urls()))
        module_permissions = set(module.get_required_permissions())
        for permission in (url_permissions | module_permissions):
            if module.__class__ in migrated_permissions:
                assert permission in migrated_permissions[module.__class__]
            else:
                assert get_permission_object_from_string(permission)


@pytest.mark.django_db
@pytest.mark.parametrize("button_class, kwargs", [
    (URLActionButton, {"url": "/test/url/"}),
    (JavaScriptActionButton, {"onclick": None}),
    (PostActionButton, {}),
    (DropdownActionButton, {"items": [DropdownItem()]}),
    (DropdownItem, {})
])
def test_toolbar_button_permissions(rf, button_class, kwargs):
    permissions = set(["shuup.add_product", "shuup.delete_product", "shuup.change_product"])

    request = rf.get("/")
    request.user = StaffUser()
    button = button_class(required_permissions=permissions, **kwargs)
    rendered_button = "".join(bit for bit in button.render(request))
    assert not rendered_button

    request.user.permissions = permissions
    rendered_button = "".join(bit for bit in button.render(request))
    assert rendered_button
