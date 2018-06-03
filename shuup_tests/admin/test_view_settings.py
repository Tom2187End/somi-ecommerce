# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

import pytest
from django.utils.http import urlencode

from shuup import configuration
from shuup.admin.modules.products.views import ProductListView
from shuup.admin.modules.settings.views import ListSettingsView
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_view_default_columns(rf, admin_user):
    shop = get_default_shop()

    view = ProductListView.as_view()

    request = apply_request_middleware(rf.get("/", {
        "jq": json.dumps({"perPage": 100, "page": 1})
    }), user=admin_user)
    response = view(request)
    assert 200 <= response.status_code < 300

    listview = ProductListView()
    assert listview.settings.default_columns == listview.default_columns

    column_names = [c.id for c in sorted(listview.columns, key=lambda x: x.id)]
    default_column_names = [c.id for c in sorted(listview.default_columns, key=lambda x: x.id)]
    assert column_names == default_column_names
    assert configuration.get(None, "view_configuration_shopproduct_name")  # name is configured
    assert listview.settings.view_configured()
    assert listview.settings.get_settings_key("name") == "view_configuration_shopproduct_name"  # we are attached to product view

    settings_view = ListSettingsView.as_view()
    view_data = {"model": "ShopProduct", "module": "shuup.core.models", "return_url": "shop_product"}
    request = rf.get("/", view_data)
    response = settings_view(request)
    assert 200 <= response.status_code < 300

    # Change configuration by posting form
    request = rf.post("/?" + urlencode(view_data), {"view_configuration_shopproduct_name": False})
    response = settings_view(request)
    assert response.status_code == 302

    assert listview.settings.get_config("name") == configuration.get(None, "view_configuration_shopproduct_name")
    assert not configuration.get(None, "view_configuration_shopproduct_name").get("active")


@pytest.mark.django_db
def test_view_saved_columns(rf):
    shop = get_default_shop()
    visible_fields = sorted(["shopproduct_id", "name", "select"])
    configuration.set(None, "view_configuration_shopproduct_saved", True)
    for field in visible_fields:
        configuration.set(None, "view_configuration_shopproduct_%s" % field, {"active": True, "ordering": 999})

    listview = ProductListView()
    column_names = [c.id for c in sorted(listview.columns, key=lambda x: x.id)]
    assert len(listview.columns) == len(visible_fields)
    assert column_names == visible_fields
