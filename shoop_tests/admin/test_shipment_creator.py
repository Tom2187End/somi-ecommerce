# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
import re

from bs4 import BeautifulSoup
from django import forms

from shoop.admin.modules.orders.views.shipment import (
    FORM_MODIFIER_PROVIDER_KEY, OrderCreateShipmentView, ShipmentFormModifier
)
from shoop.apps.provides import override_provides
from shoop.core.models import Order
from shoop.testing.factories import (
    create_order_with_product, create_product, get_default_shop,
    get_default_supplier
)
from shoop.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_shipment_creating_view_get(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(sku="test-sku", shop=shop, supplier=supplier, default_price=3.33)
    quantity = 1
    order = create_order_with_product(
        product, supplier, quantity=quantity, taxless_base_unit_price=1, shop=shop)

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view = OrderCreateShipmentView.as_view()
    response = view(request, pk=order.pk).render()
    assert response.status_code == 200

    # Should contain supplier input and input for product
    soup = BeautifulSoup(response.content)
    assert soup.find("input", {"id": "id_q_%s" % product.pk})
    assert soup.find("select", {"id": "id_supplier"})


@pytest.mark.django_db
def test_shipment_creating_view_post(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(sku="test-sku", shop=shop, supplier=supplier, default_price=3.33)
    order = create_order_with_product(product, supplier, quantity=1, taxless_base_unit_price=1, shop=shop)

    data = {
        "q_%s" % product.pk: 1,
        "supplier": supplier.pk
    }
    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
    view = OrderCreateShipmentView.as_view()
    response = view(request, pk=order.pk)
    assert response.status_code == 302

    # Order should have shipment
    assert order.shipments.count() == 1
    shipment = order.shipments.first()
    assert shipment.supplier_id == supplier.id
    assert shipment.products.count() == 1
    assert shipment.products.first().product_id == product.id


@pytest.mark.django_db
def test_extending_shipment_with_extra_fields(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(sku="test-sku", shop=shop, supplier=supplier, default_price=3.33)
    quantity = 1
    order = create_order_with_product(
        product, supplier, quantity=quantity, taxless_base_unit_price=1, shop=shop)

    extend_form_class = "shoop_tests.admin.test_shipment_creator.ShipmentFormModifierTest"
    with override_provides(FORM_MODIFIER_PROVIDER_KEY, [extend_form_class]):
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        view = OrderCreateShipmentView.as_view()
        response = view(request, pk=order.pk).render()
        assert response.status_code == 200

        # Should contain supplier input, input for product and input for phone
        soup = BeautifulSoup(response.content)
        assert soup.find("input", {"id": "id_q_%s" % product.pk})
        assert soup.find("select", {"id": "id_supplier"})
        assert soup.find("input", {"id": "id_phone"})


@pytest.mark.django_db
def test_extending_shipment_clean_hook(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(sku="test-sku", shop=shop, supplier=supplier, default_price=3.33)
    quantity = 1
    order = create_order_with_product(
        product, supplier, quantity=quantity, taxless_base_unit_price=1, shop=shop)

    extend_form_class = "shoop_tests.admin.test_shipment_creator.ShipmentFormModifierTest"
    with override_provides(FORM_MODIFIER_PROVIDER_KEY, [extend_form_class]):
        data = {
            "q_%s" % product.pk: 1,
            "supplier": supplier.pk,
            "phone": "911"
        }
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        view = OrderCreateShipmentView.as_view()
        response = view(request, pk=order.pk).render()
        assert response.status_code == 200
        soup = BeautifulSoup(response.content)
        assert soup.body.findAll(text=re.compile("Phone number should start with country code!"))


@pytest.mark.django_db
def test_extending_shipment_form_valid_hook(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(sku="test-sku", shop=shop, supplier=supplier, default_price=3.33)
    quantity = 1
    order = create_order_with_product(
        product, supplier, quantity=quantity, taxless_base_unit_price=1, shop=shop)

    extend_form_class = "shoop_tests.admin.test_shipment_creator.ShipmentFormModifierTest"
    with override_provides(FORM_MODIFIER_PROVIDER_KEY, [extend_form_class]):
        phone_number = "+358911"
        data = {
            "q_%s" % product.pk: 1,
            "supplier": supplier.pk,
            "phone": phone_number
        }
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
        view = OrderCreateShipmentView.as_view()
        response = view(request, pk=order.pk)
        assert response.status_code == 302

        # Order should now have shipment, but let's re fetch it first
        order = Order.objects.get(pk=order.pk)
        assert order.shipments.count() == 1

        shipment = order.shipments.first()
        assert order.shipping_data.get(shipment.identifier).get("phone") == phone_number
        assert shipment.supplier_id == supplier.id
        assert shipment.products.count() == 1
        assert shipment.products.first().product_id == product.id


class ShipmentFormModifierTest(ShipmentFormModifier):
    def get_extra_fields(self, order):
        return [("phone", forms.CharField(label="Phone", max_length=64, required=False))]

    def clean_hook(self, form):
        cleaned_data = form.cleaned_data
        phone = cleaned_data.get("phone")
        if not phone.startswith("+"):
            form.add_error("phone", "Phone number should start with country code!")

    def form_valid_hook(self, form, shipment):
        data = form.cleaned_data
        if data.get("phone"):
            shipping_data = shipment.order.shipping_data or {}
            shipping_data[shipment.identifier] = {"phone": data.get("phone")}
            shipment.order.shipping_data = shipping_data
            shipment.order.save()
