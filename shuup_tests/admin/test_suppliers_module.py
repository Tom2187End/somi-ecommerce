# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

import pytest
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from shuup.admin.modules.suppliers.views import (
    SupplierEditView, SupplierListView
)
from shuup.core.models import Supplier, SupplierType
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_suppliers_list(rf, admin_user):
    shop = factories.get_default_shop()
    shop2 = factories.get_shop(identifier="shop2")

    supplier1 = Supplier.objects.create(name="supplier1")
    supplier2 = Supplier.objects.create(name="supplier1")
    supplier3 = Supplier.objects.create(name="supplier1")
    # only supplier 1 has shop
    supplier1.shops.add(shop)
    supplier3.shops.add(shop2)

    list_view = SupplierListView.as_view()

    staff_user = factories.create_random_user("en", is_staff=True)
    shop.staff_members.add(staff_user)

    for user in [admin_user, staff_user]:
        request = apply_request_middleware(rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=user)
        response = list_view(request)
        data = json.loads(response.content.decode("utf-8"))
        ids = [sup["_id"] for sup in data["items"]]
        assert supplier1.id in ids
        assert supplier2.id in ids


@pytest.mark.django_db
def test_suppliers_edit(rf, admin_user):
    shop = factories.get_default_shop()
    edit_view = SupplierEditView.as_view()

    staff_user = factories.create_random_user("en", is_staff=True)
    shop.staff_members.add(staff_user)

    with override_settings(SHUUP_ENABLE_MULTIPLE_SUPPLIERS=True):
        for index, user in enumerate([admin_user, staff_user]):
            payload = {
                "base-name": "Supplier Name %d" % index,
                "base-description__en": "Supplier Description %d" % index,
                "base-type": SupplierType.INTERNAL.value,
                "base-module_identifier": "",
                "base-shops": shop.pk,
                "base-enabled": "on",
                "base-logo": "",
                "base-is_approved": "on",
                "address-name": "Address Name %d" % index,
                "address-email": "email@example.com",
                "address-phone": "23742578329",
                "address-tax_number": "ABC123",
                "address-street": "Streetz",
                "address-postal_code": "90014",
                "address-city": "Los Angeles",
                "address-region_code": "CA",
                "address-country": "US"
            }

            request = apply_request_middleware(rf.post("/", payload), user=user)
            response = edit_view(request)
            assert response.status_code == 302
            sup = Supplier.objects.last()
            assert response.url == reverse("shuup_admin:supplier.edit", kwargs=dict(pk=sup.pk))
            assert sup.name == payload["base-name"]
            assert sup.description == payload["base-description__en"]
            assert sup.shops.count() == 1
            assert sup.enabled
            assert sup.is_approved
            assert sup.contact_address.name == payload["address-name"]
