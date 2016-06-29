# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import random

import pytest
from django.core.urlresolvers import reverse

from shuup.core.models import Order, PaymentStatus
from shuup.testing.factories import (
    create_default_order_statuses, get_address, get_default_payment_method,
    get_default_shipping_method, get_default_shop, get_default_supplier,
    get_default_tax_class
)
from shuup.testing.mock_population import populate_if_required
from shuup.testing.models import (
    CarrierWithCheckoutPhase, PaymentWithCheckoutPhase
)
from shuup.testing.soup_utils import extract_form_fields
from shuup_tests.utils import SmartClient


def fill_address_inputs(soup, with_company=False):
    inputs = {}
    test_address = get_address()
    for key, value in extract_form_fields(soup.find('form', id='addresses')).items():
        if not value:
            if key in ("order-tax_number", "order-company_name"):
                continue
            if key.startswith("shipping-") or key.startswith("billing-"):
                bit = key.split("-")[1]
                value = getattr(test_address, bit, None)
            if not value and "email" in key:
                value = "test%d@example.shuup.com" % random.random()
            if not value:
                value = "test"
        inputs[key] = value

    if with_company:
        inputs["company-tax_number"] = "FI1234567-1"
        inputs["company-company_name"] = "Example Oy"
    else:
        inputs = dict((k, v) for (k, v) in inputs.items() if not k.startswith("company-"))

    return inputs


def _populate_client_basket(client):
    index = client.soup("/")
    product_links = index.find_all("a", rel="product-detail")
    assert product_links
    product_detail_path = product_links[0]["href"]
    assert product_detail_path
    product_detail_soup = client.soup(product_detail_path)
    inputs = extract_form_fields(product_detail_soup)
    basket_path = reverse("shuup:basket")
    for i in range(3):  # Add the same product thrice
        add_to_basket_resp = client.post(basket_path, data={
            "command": "add",
            "product_id": inputs["product_id"],
            "quantity": 1,
            "supplier": get_default_supplier().pk
        })
        assert add_to_basket_resp.status_code < 400
    basket_soup = client.soup(basket_path)
    assert b'no such element' not in basket_soup.renderContents(), 'All product details are not rendered correctly'


def _get_payment_method_with_phase():
    processor = PaymentWithCheckoutPhase.objects.create(
        identifier="processor_with_phase", enabled=True)
    assert isinstance(processor, PaymentWithCheckoutPhase)
    return processor.create_service(
        None,
        identifier="payment_with_phase",
        shop=get_default_shop(),
        name="Test method with phase",
        enabled=True,
        tax_class=get_default_tax_class())


def _get_shipping_method_with_phase():
    carrier = CarrierWithCheckoutPhase.objects.create(
        identifier="carrier_with_phase", enabled=True)
    assert isinstance(carrier, CarrierWithCheckoutPhase)
    return carrier.create_service(
        None,
        identifier="carrier_with_phase",
        shop=get_default_shop(),
        name="Test method with phase",
        enabled=True,
        tax_class=get_default_tax_class())


@pytest.mark.django_db
@pytest.mark.parametrize("with_company", [False, True])
def test_basic_order_flow(with_company):
    create_default_order_statuses()
    n_orders_pre = Order.objects.count()
    populate_if_required()
    c = SmartClient()
    _populate_client_basket(c)

    addresses_path = reverse("shuup:checkout", kwargs={"phase": "addresses"})
    addresses_soup = c.soup(addresses_path)
    inputs = fill_address_inputs(addresses_soup, with_company=with_company)
    response = c.post(addresses_path, data=inputs)
    assert response.status_code == 302  # Should redirect forth

    methods_path = reverse("shuup:checkout", kwargs={"phase": "methods"})
    methods_soup = c.soup(methods_path)
    assert c.post(methods_path, data=extract_form_fields(methods_soup)).status_code == 302  # Should redirect forth

    confirm_path = reverse("shuup:checkout", kwargs={"phase": "confirm"})
    confirm_soup = c.soup(confirm_path)
    assert c.post(confirm_path, data=extract_form_fields(confirm_soup)).status_code == 302  # Should redirect forth

    n_orders_post = Order.objects.count()
    assert n_orders_post > n_orders_pre, "order was created"


@pytest.mark.django_db
@pytest.mark.parametrize("get_shipping_method,shipping_data,get_payment_method,payment_data", [
    (get_default_shipping_method, None, _get_payment_method_with_phase, {"input_field": True}),
    (_get_shipping_method_with_phase, {"input_field": "20540"}, get_default_payment_method, None),
    (_get_shipping_method_with_phase, {"input_field": "20540"}, _get_payment_method_with_phase, {"input_field": True}),
])
def test_order_flow_with_phases(get_shipping_method, shipping_data, get_payment_method, payment_data):
    create_default_order_statuses()
    populate_if_required()
    c = SmartClient()
    _populate_client_basket(c)

    # Create methods
    shipping_method = get_shipping_method()
    payment_method = get_payment_method()

    # Resolve paths
    addresses_path = reverse("shuup:checkout", kwargs={"phase": "addresses"})
    methods_path = reverse("shuup:checkout", kwargs={"phase": "methods"})
    shipping_path = reverse("shuup:checkout", kwargs={"phase": "shipping"})
    payment_path = reverse("shuup:checkout", kwargs={"phase": "payment"})
    confirm_path = reverse("shuup:checkout", kwargs={"phase": "confirm"})

    # Phase: Addresses
    addresses_soup = c.soup(addresses_path)
    inputs = fill_address_inputs(addresses_soup, with_company=False)
    response = c.post(addresses_path, data=inputs)
    assert response.status_code == 302, "Address phase should redirect forth to methods"

    # Phase: Methods
    response = c.get(methods_path)
    assert response.status_code == 200
    response = c.post(
        methods_path,
        data={
            "shipping_method": shipping_method.pk,
            "payment_method": payment_method.pk
        }
    )
    assert response.status_code == 302, "Methods phase should redirect forth"

    if isinstance(shipping_method.carrier, CarrierWithCheckoutPhase):
        # Phase: Shipping
        response = c.get(shipping_path)
        assert response.status_code == 200
        response = c.post(shipping_path, data=shipping_data)
        assert response.status_code == 302, "Payments phase should redirect forth"

    if isinstance(payment_method.payment_processor, PaymentWithCheckoutPhase):
        # Phase: payment
        response = c.get(payment_path)
        assert response.status_code == 200
        response = c.post(payment_path, data=payment_data)
        assert response.status_code == 302, "Payments phase should redirect forth"

    # Phase: Confirm
    assert Order.objects.count() == 0
    confirm_soup = c.soup(confirm_path)
    response = c.post(confirm_path, data=extract_form_fields(confirm_soup))
    assert response.status_code == 302, "Confirm should redirect forth"

    order = Order.objects.first()

    if isinstance(shipping_method.carrier, CarrierWithCheckoutPhase):
        assert order.shipping_data.get("input_value") == "20540"

    if isinstance(payment_method.payment_processor, PaymentWithCheckoutPhase):
        assert order.payment_data.get("input_value")
        assert order.payment_status == PaymentStatus.NOT_PAID
        # Resolve order specific paths (payment and complete)
        process_payment_path = reverse(
            "shuup:order_process_payment",
            kwargs={"pk": order.pk, "key": order.key})
        process_payment_return_path = reverse(
            "shuup:order_process_payment_return",
            kwargs={"pk": order.pk, "key": order.key})
        order_complete_path = reverse(
            "shuup:order_complete",
            kwargs={"pk": order.pk, "key": order.key})

        # Check confirm redirection to payment page
        assert response.url.endswith(process_payment_path), (
            "Confirm should have redirected to payment page")

        # Visit payment page
        response = c.get(process_payment_path)
        assert response.status_code == 302, "Payment page should redirect forth"
        assert response.url.endswith(process_payment_return_path)

        # Check payment return
        response = c.get(process_payment_return_path)
        assert response.status_code == 302, "Payment return should redirect forth"
        assert response.url.endswith(order_complete_path)

        # Check payment status has changed to DEFERRED
        order = Order.objects.get(pk=order.pk)  # reload
        assert order.payment_status == PaymentStatus.DEFERRED
