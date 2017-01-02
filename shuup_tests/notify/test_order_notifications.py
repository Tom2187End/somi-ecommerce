# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import random

import pytest
from django.core import mail
from django.core.urlresolvers import reverse
from django.utils.translation import activate

from shuup.core import cache
from shuup.core.defaults.order_statuses import create_default_order_statuses
from shuup.core.models import (
    get_person_contact, MutableAddress, Order, OrderLineType, Product,
    StockBehavior
)
from shuup.core.order_creator import OrderCreator
from shuup.core.pricing import get_pricing_module
from shuup.notify.models import Script
from shuup.testing.factories import (
    create_product, create_random_order, create_random_person,
    get_default_category, get_default_product, get_default_supplier,
    get_default_tax_class, get_initial_order_status, get_shop
)
from shuup.testing.mock_population import populate_if_required
from shuup.testing.soup_utils import extract_form_fields
from shuup_tests.admin.test_order_creator import (
    get_frontend_order_state, get_order_from_state
)
from shuup_tests.front.test_checkout_flow import (
    _populate_client_basket, fill_address_inputs
)
from shuup_tests.functional.test_refunds import (
    _add_basket_campaign, _add_catalog_campaign, _add_taxes, _get_product_data,
    INITIAL_PRODUCT_QUANTITY
)
from shuup_tests.simple_supplier.utils import get_simple_supplier
from shuup_tests.utils import SmartClient
from shuup_tests.utils.basketish_order_source import BasketishOrderSource
from shuup_tests.utils.fixtures import (
    regular_user, REGULAR_USER_PASSWORD, REGULAR_USER_USERNAME
)

STEP_DATA = [{
    "cond_op": "all",
    "enabled": True,
    "conditions": [{
        "v1": {"variable":"language"},
        "template_data": {},
        "v2": {"variable":"language"},
        "identifier":"language_equal"
    }],
    "next": "continue",
    "actions": [{
        "fallback_language": {
            "constant": "FI"
        },
        "template_data": {
            "en": {
                "body": "english",
                "content_type": "plain",
                "subject": "english"
            },
            "fi": {
                "body": "finnish",
                "content_type": "plain",
                "subject": "finnish"
            },
            "ja": {
                "body": "japan",
                "content_type": "plain",
                "subject": "japan"
            },
            "zh-hans": {
                "body": "china",
                "content_type": "plain",
                "subject": "china"
            },
            "pt-br": {
                "body": "brazil",
                "content_type": "plain",
                "subject": "brazil"
            },
            "it": {
                "body": "italia",
                "content_type": "plain",
                "subject": "italia"
            }
        },
        "identifier": "send_email",
        "language": {
            "variable": "language"
        },
        "recipient": {
            "constant": "janne@shuup.com"
        }
    }]
}]

DEFAULT_ADDRESS_DATA = dict(
    prefix="Sir",
    name=u"Dog Hello",
    suffix=", Esq.",
    postal_code="K9N",
    street="Woof Ave.",
    city="Dog Fort",
    country="GB"
)

def get_address(**overrides):
    data = dict(DEFAULT_ADDRESS_DATA, **overrides)
    return MutableAddress.from_data(data)


def get_test_script(name, identifier):
    sc = Script.objects.create(name=name, event_identifier=identifier, enabled=True)
    sc.set_serialized_steps(STEP_DATA)
    sc.save()
    return sc


def _get_custom_order(regular_user, **kwargs):
    prices_include_tax = kwargs.pop("prices_include_tax", False)
    include_basket_campaign = kwargs.pop("include_basket_campaign", False)
    include_catalog_campaign = kwargs.pop("include_catalog_campaign", False)

    shop = get_shop(prices_include_tax=prices_include_tax)
    supplier = get_simple_supplier()

    if include_basket_campaign:
        _add_basket_campaign(shop)

    if include_catalog_campaign:
        _add_catalog_campaign(shop)
    _add_taxes()

    contact = get_person_contact(regular_user)
    source = BasketishOrderSource(shop)
    source.status = get_initial_order_status()
    source.customer = contact

    ctx = get_pricing_module().get_context_from_data(shop, contact)
    for product_data in _get_product_data():
        quantity = product_data.pop("quantity")
        product = create_product(
            sku=product_data.pop("sku"),
            shop=shop,
            supplier=supplier,
            stock_behavior=StockBehavior.STOCKED,
            tax_class=get_default_tax_class(),
            **product_data)
        shop_product = product.get_shop_instance(shop)
        shop_product.categories.add(get_default_category())
        shop_product.save()
        supplier.adjust_stock(product.id, INITIAL_PRODUCT_QUANTITY)
        pi = product.get_price_info(ctx)
        source.add_line(
            type=OrderLineType.PRODUCT,
            product=product,
            supplier=supplier,
            quantity=quantity,
            base_unit_price=pi.base_unit_price,
            discount_amount=pi.discount_amount
        )

    oc = OrderCreator()
    order = oc.create_order(source)
    return order


def fill_address_inputs(soup, address, with_company=False):
    inputs = {}
    for key, value in extract_form_fields(soup.find('form', id='addresses')).items():
        if not value:
            if key in ("order-tax_number", "order-company_name"):
                continue
            if key.startswith("shipping-") or key.startswith("billing-"):
                bit = key.split("-")[1]
                value = getattr(address, bit, None)
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

@pytest.mark.django_db
def test_order_received(rf, regular_user):
    activate("en")
    get_default_product()
    get_default_supplier()
    get_test_script("test script", "order_received")

    template_data = STEP_DATA[0]["actions"][0]["template_data"]
    for lang in ["en", "fi"]:
        n_outbox_pre = len(mail.outbox)
        customer = create_random_person(locale=lang)
        create_random_order(customer)
        assert (len(mail.outbox) == n_outbox_pre + 1), "Sending email failed"
        latest_mail = mail.outbox[-1]
        assert latest_mail.subject == template_data[lang]["subject"], "Subject doesn't match"
        assert latest_mail.body == template_data[lang]["body"], "Body doesn't match"


@pytest.mark.django_db
def test_order_received_admin(rf, admin_user):
    get_test_script("test script", "order_received")
    template_data = STEP_DATA[0]["actions"][0]["template_data"]
    for lang in ["en", "fi"]:
        get_initial_order_status()  # Needed for the API
        n_outbox_pre = len(mail.outbox)
        contact = create_random_person(locale=lang, minimum_name_comp_len=5)
        get_order_from_state(get_frontend_order_state(contact), admin_user)
        assert (len(mail.outbox) == n_outbox_pre + 1), "Sending email failed"
        latest_mail = mail.outbox[-1]
        assert latest_mail.subject == template_data[lang]["subject"], "Subject doesn't match"
        assert latest_mail.body == template_data[lang]["body"], "Body doesn't match"


@pytest.mark.django_db
@pytest.mark.parametrize("with_company", [False, True])
def test_basic_order_flow_not_registered(with_company):
    cache.clear()
    create_default_order_statuses()
    n_orders_pre = Order.objects.count()
    populate_if_required()
    get_test_script("test script", "order_received")
    # paths
    addresses_path = reverse("shuup:checkout", kwargs={"phase": "addresses"})
    methods_path = reverse("shuup:checkout", kwargs={"phase": "methods"})
    confirm_path = reverse("shuup:checkout", kwargs={"phase": "confirm"})

    template_data = STEP_DATA[0]["actions"][0]["template_data"]

    LANG_CODE = {
        "en": "US",
        "fi": "FI"
    }

    for lang in ["en", "fi"]:
        n_outbox_pre = len(mail.outbox)
        c = SmartClient()
        product_ids = _populate_client_basket(c)

        addresses_soup = c.soup(addresses_path)
        address = get_address(country=LANG_CODE[lang])

        inputs = fill_address_inputs(addresses_soup, address, with_company=with_company)
        response = c.post(addresses_path, data=inputs)
        assert response.status_code == 302  # Should redirect forth

        methods_soup = c.soup(methods_path)
        assert c.post(methods_path, data=extract_form_fields(methods_soup)).status_code == 302  # Should redirect forth

        confirm_soup = c.soup(confirm_path)
        Product.objects.get(pk=product_ids[0]).soft_delete()
        assert c.post(confirm_path, data=extract_form_fields(confirm_soup)).status_code == 200  # user needs to reconfirm
        data = extract_form_fields(confirm_soup)
        data['product_ids'] = ','.join(product_ids[1:])
        assert c.post(confirm_path, data=data).status_code == 302  # Should redirect forth

        n_orders_post = Order.objects.count()
        assert n_orders_post > n_orders_pre, "order was created"
        assert (len(mail.outbox) == n_outbox_pre + 1), "Sending email failed"
        latest_mail = mail.outbox[-1]

        # mail is always sent in fallback language since user is not registered
        assert latest_mail.subject == template_data["en"]["subject"], "Subject doesn't match"
        assert latest_mail.body == template_data["en"]["body"], "Body doesn't match"


@pytest.mark.django_db
def test_basic_order_flow_registered(regular_user):
    cache.clear()
    create_default_order_statuses()
    n_orders_pre = Order.objects.count()
    populate_if_required()
    get_test_script("test script", "order_received")
    # paths
    addresses_path = reverse("shuup:checkout", kwargs={"phase": "addresses"})
    methods_path = reverse("shuup:checkout", kwargs={"phase": "methods"})
    confirm_path = reverse("shuup:checkout", kwargs={"phase": "confirm"})

    template_data = STEP_DATA[0]["actions"][0]["template_data"]

    LANG_CODE = {
        "en": "US",
        "fi": "FI"
    }

    for lang in ["en", "fi"]:
        n_outbox_pre = len(mail.outbox)
        contact = get_person_contact(regular_user)
        contact.language = lang
        contact.save()

        c = SmartClient()
        c.login(username=REGULAR_USER_USERNAME, password=REGULAR_USER_PASSWORD)

        product_ids = _populate_client_basket(c)

        addresses_soup = c.soup(addresses_path)
        address = get_address(country=LANG_CODE[lang])

        inputs = fill_address_inputs(addresses_soup, address)
        response = c.post(addresses_path, data=inputs)
        assert response.status_code == 302  # Should redirect forth

        methods_soup = c.soup(methods_path)
        assert c.post(methods_path, data=extract_form_fields(methods_soup)).status_code == 302  # Should redirect forth

        confirm_soup = c.soup(confirm_path)
        Product.objects.get(pk=product_ids[0]).soft_delete()
        assert c.post(confirm_path, data=extract_form_fields(confirm_soup)).status_code == 200  # user needs to reconfirm
        data = extract_form_fields(confirm_soup)
        data['product_ids'] = ','.join(product_ids[1:])
        assert c.post(confirm_path, data=data).status_code == 302  # Should redirect forth

        n_orders_post = Order.objects.count()
        assert n_orders_post > n_orders_pre, "order was created"
        assert (len(mail.outbox) == n_outbox_pre + 1), "Sending email failed"
        latest_mail = mail.outbox[-1]

        # mail is always sent in fallback language since user is not registered
        assert latest_mail.subject == template_data[lang]["subject"], "Subject doesn't match"
        assert latest_mail.body == template_data[lang]["body"], "Body doesn't match"
