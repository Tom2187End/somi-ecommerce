# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test.utils import override_settings

import pytest
from shoop.apps.provides import override_provides
from shoop.core.methods.base import BaseShippingMethodModule
from shoop.core.models.contacts import PersonContact, get_person_contact
from shoop.core.models.methods import ShippingMethod, PaymentMethod
from shoop.core.models.order_lines import OrderLineType
from shoop.core.order_creator.source import SourceLine
from shoop.core.pricing import TaxfulPrice, TaxlessPrice
from shoop.testing.factories import (
    get_address, get_default_shop, get_default_product, get_default_supplier, get_default_tax_class,
    create_product
)
from shoop_tests.utils.basketish_order_source import BasketishOrderSource


class ExpensiveSwedenShippingModule(BaseShippingMethodModule):
    identifier = "expensive_sweden"
    name = "Expensive Sweden Shipping"

    def get_effective_name(self, source, **kwargs):
        return u"Expenseefe-a Svedee Sheepping"

    def get_effective_price(self, source, **kwargs):
        if source.shipping_address and source.shipping_address.country == "SE":
            return TaxfulPrice("5.00")
        return TaxfulPrice("4.00")

    def get_validation_errors(self, source, **kwargs):
        for error in super(ExpensiveSwedenShippingModule, self).get_validation_errors(source, **kwargs):
            # The following line is no cover because the parent class doesn't necessarily error out
            yield error  # pragma: no cover


        if source.shipping_address and source.shipping_address.country == "FI":
            yield ValidationError("Veell nut sheep unytheeng tu Feenlund!", code="we_no_speak_finnish")


SHIPPING_METHOD_SPEC = "%s:%s" % (__name__, ExpensiveSwedenShippingModule.__name__)


def get_expensive_sweden_shipping_method():
    sm = ShippingMethod(
        identifier=ExpensiveSwedenShippingModule.identifier,
        module_identifier=ExpensiveSwedenShippingModule.identifier,
        tax_class=get_default_tax_class()
    )
    sm.module_data = {
        "min_weight": "0.11000000",
        "max_weight": "3.00000000",
        "price_waiver_product_minimum": "370"
    }
    sm.save()
    return sm

def override_provides_for_expensive_sweden_shipping_method():
    return override_provides("shipping_method_module", [SHIPPING_METHOD_SPEC])

@pytest.mark.django_db
@pytest.mark.parametrize("country", ["FI", "SE", "NL", "NO"])
def test_methods(admin_user, country):
    contact = get_person_contact(admin_user)
    source = BasketishOrderSource(lines=[
        SourceLine(
            type=OrderLineType.PRODUCT,
            product=get_default_product(),
            supplier=get_default_supplier(),
            quantity=1,
            unit_price=TaxlessPrice(10),
            weight=Decimal("0.2")
        )
    ])
    billing_address = get_address()
    shipping_address = get_address(name="Shippy Doge", country=country)
    source.shop = get_default_shop()
    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = contact

    with override_provides_for_expensive_sweden_shipping_method():
        source.shipping_method = get_expensive_sweden_shipping_method()
        source.payment_method = PaymentMethod.objects.create(identifier="neat",
                                                             module_data={"price": 4},
                                                             tax_class=get_default_tax_class())
        assert source.shipping_method_id
        assert source.payment_method_id

        errors = list(source.get_validation_errors())

        if country == "FI":  # "Expenseefe-a Svedee Sheepping" will not allow shipping to Finland, let's see if that holds true
            assert any([ve.code == "we_no_speak_finnish" for ve in errors])
            return  # Shouldn't try the rest if we got an error here
        else:
            assert not errors

        final_lines = list(source.get_final_lines())

        assert any(line.type == OrderLineType.SHIPPING for line in final_lines)

        # TODO: (TAX) for some reason SourceLine.taxless_total_price property has been removed
        # I think it should be implemented back like in OrderLine / janne

        for line in final_lines:
            if line.type == OrderLineType.SHIPPING:
                if country == "SE":  # We _are_ using Expenseefe-a Svedee Sheepping after all.
                    assert line.taxless_total_price == TaxlessPrice("5.00")
                else:
                    assert line.taxless_total_price == TaxlessPrice("4.00")
                assert line.text == u"Expenseefe-a Svedee Sheepping"
            if line.type == OrderLineType.PAYMENT:
                assert line.taxless_total_price == TaxlessPrice("4")


@pytest.mark.django_db
def test_method_list(admin_user):
    with override_provides_for_expensive_sweden_shipping_method():
        assert any(name == "Expensive Sweden Shipping" for (spec, name) in ShippingMethod.get_module_choices())

@pytest.mark.django_db
def test_waiver():
    sm = ShippingMethod(name="Waivey", tax_class=get_default_tax_class(),
                        module_data={
                            "price_waiver_product_minimum": "370",
                            "price": "100"
                        })
    source = BasketishOrderSource()
    assert not source.prices_include_tax()
    assert sm.get_effective_name(source) == u"Waivey"
    assert sm.get_effective_price(source) == TaxlessPrice(100)
    source.lines = [
        SourceLine(
            type=OrderLineType.PRODUCT,
            product=get_default_product(),
            unit_price=TaxlessPrice(400),
            quantity=1
        )
    ]
    assert sm.get_effective_price(source) == TaxlessPrice(0)


@pytest.mark.django_db
def test_weight_limits():
    sm = ShippingMethod(tax_class=get_default_tax_class())
    sm.module_data = {"min_weight": "100", "max_weight": "500"}
    source = BasketishOrderSource()
    assert any(ve.code == "min_weight" for ve in sm.get_validation_errors(source))
    source.lines = [SourceLine(type=OrderLineType.PRODUCT, weight=600)]
    assert any(ve.code == "max_weight" for ve in sm.get_validation_errors(source))


# TODO: (TAX) Taxing of shipping methods
# @pytest.mark.django_db
# def test_tax():
#     sm = ShippingMethod(tax_class=None, module_data={"taxless_price": 50})
#     source = BasketishOrderSource()
#     source.lines = [  # Since `tax_class` is None, the highest tax percentage in the order should be used:
#                       SourceLine(type=OrderLineType.PRODUCT, tax_rate=Decimal("0.8")),
#                       SourceLine(type=OrderLineType.PRODUCT, tax_rate=Decimal("0.3")),
#     ]
#     line = list(sm.get_source_lines(source))[0]
#     assert line.tax_rate == Decimal("0.8")

#     sm.tax_class = get_default_tax_group()
#     line = list(sm.get_source_lines(source))[0]
#     assert line.tax_rate == sm.tax_class.tax_rate


@pytest.mark.django_db
def test_limited_methods():
    """
    Test that products can declare that they limit available shipping methods.
    """
    unique_shipping_method = ShippingMethod(tax_class=get_default_tax_class(), module_data={"taxless_price": 0})
    unique_shipping_method.save()
    shop = get_default_shop()
    common_product = create_product(sku="SH_COMMON", shop=shop)  # A product that does not limit shipping methods
    unique_product = create_product(sku="SH_UNIQUE", shop=shop)  # A product that only supports unique_shipping_method
    unique_shop_product = unique_product.get_shop_instance(shop)
    unique_shop_product.limit_shipping_methods = True
    unique_shop_product.shipping_methods.add(unique_shipping_method)
    unique_shop_product.save()
    impossible_product = create_product(sku="SH_IMP", shop=shop)  # A product that can't be shipped at all
    imp_shop_product = impossible_product.get_shop_instance(shop)
    imp_shop_product.limit_shipping_methods = True
    imp_shop_product.save()
    for product_ids, method_ids in [
        ((common_product.pk, unique_product.pk), (unique_shipping_method.pk,)),
        ((common_product.pk,), ShippingMethod.objects.values_list("pk", flat=True)),
        ((unique_product.pk,), (unique_shipping_method.pk,)),
        ((unique_product.pk, impossible_product.pk,), ()),
        ((common_product.pk, impossible_product.pk,), ()),
    ]:
        product_ids = set(product_ids)
        assert ShippingMethod.objects.available_ids(shop_id=shop.id, product_ids=product_ids) == set(method_ids)
