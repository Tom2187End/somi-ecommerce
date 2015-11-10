# -*- coding: utf-8 -*-
import json

from django.test import RequestFactory
from shoop.core.models import Order
from shoop.testing.factories import (
    create_random_person, create_product,
    get_default_supplier, get_default_shop,
    get_default_shipping_method, get_initial_order_status
)
from shoop_tests.utils import printable_gibberish, apply_request_middleware, assert_contains
from shoop.admin.modules.orders.views.create import OrderCreateView


def get_frontend_order_state(contact, valid_lines=True):
    """
    Get a dict structure mirroring what the frontend JavaScript would submit.
    :type contact: Contact|None
    """

    shop = get_default_shop()
    product = create_product(
        sku=printable_gibberish(),
        supplier=get_default_supplier(),
        shop=shop
    )
    if valid_lines:
        lines = [
            {"id": "x", "type": "product", "product": {"id": product.id}, "quantity": "32", "unitPrice": 50},
            {"id": "y", "type": "other", "sku": "hello", "text": "A greeting", "quantity": 1, "unitPrice": "5.5"},
            {"id": "z", "type": "text", "text": "This was an order!", "quantity": 0},
        ]
    else:
        unshopped_product = create_product(sku=printable_gibberish(), supplier=get_default_supplier())
        lines = [
            {"id": "x", "type": "product"},  # no product?
            {"id": "x", "type": "product", "product": {"id": unshopped_product.id}},  # not in this shop?
            {"id": "y", "type": "product", "product": {"id": -product.id}},  # invalid product?
            {"id": "z", "type": "other", "quantity": 1, "unitPrice": "q"},  # what's that price?
        ]

    state = {
        "customer": {"id": contact.id if contact else None},
        "lines": lines,
        "methods": {
            "shippingMethodId": get_default_shipping_method().id,
            "paymentMethodId": None,
        },
        "shop": {
            "id": shop.id
        }
    }
    return state


def get_frontend_create_request(state, user):
    json_data = json.dumps({"state": state})
    return apply_request_middleware(RequestFactory().post(
        "/",
        data=json_data,
        content_type="application/json; charset=UTF-8",
        QUERY_STRING="command=create"
    ), user=user)


def test_order_creator_valid(rf, admin_user):
    get_initial_order_status()  # Needed for the API
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    request = get_frontend_create_request(get_frontend_order_state(contact), admin_user)
    response = OrderCreateView.as_view()(request)
    assert_contains(response, "orderIdentifier")  # this checks for status codes as a side effect
    data = json.loads(response.content.decode("utf8"))
    order = Order.objects.get(identifier=data["orderIdentifier"])
    assert order.lines.count() == 4  # 3 submitted, one for the shipping method
    assert order.creator == admin_user
    assert order.customer == contact


def test_order_creator_invalid_base_data(rf, admin_user):
    get_initial_order_status()  # Needed for the API
    state = get_frontend_order_state(contact=None)
    # Remove some critical data...
    state["customer"]["id"] = None
    state["shop"]["id"] = None
    request = get_frontend_create_request(state, admin_user)
    response = OrderCreateView.as_view()(request)
    assert_contains(response, "errorMessage", status_code=400)


def test_order_creator_invalid_line_data(rf, admin_user):
    get_initial_order_status()  # Needed for the API
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    state = get_frontend_order_state(contact=contact, valid_lines=False)
    request = get_frontend_create_request(state, admin_user)
    response = OrderCreateView.as_view()(request)
    # Let's see that we get a cornucopia of trouble:
    assert_contains(response, "does not exist", status_code=400)
    assert_contains(response, "does not have a product", status_code=400)
    assert_contains(response, "is not available", status_code=400)
    assert_contains(response, "The price", status_code=400)
    assert_contains(response, "The quantity", status_code=400)


def test_order_creator_view_GET(rf, admin_user):
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = OrderCreateView.as_view()(request)
    assert_contains(response, "shippingMethods")  # in the config
    assert_contains(response, "shops")  # in the config


def test_order_creator_view_invalid_command(rf, admin_user):
    get_default_shop()
    request = apply_request_middleware(rf.get("/", {"command": printable_gibberish()}), user=admin_user)
    response = OrderCreateView.as_view()(request)
    assert_contains(response, "unknown command", status_code=400)


def test_order_creator_product_data(rf, admin_user):
    shop = get_default_shop()
    product = create_product(sku=printable_gibberish(), supplier=get_default_supplier(), shop=shop)
    request = apply_request_middleware(rf.get("/", {
        "command": "product_data",
        "shop_id": shop.id,
        "id": product.id,
    }), user=admin_user)
    response = OrderCreateView.as_view()(request)
    assert_contains(response, "taxClass")
    assert_contains(response, "sku")
    assert_contains(response, product.sku)
