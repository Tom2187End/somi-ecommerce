# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from decimal import Decimal

from django.test.utils import override_settings
import pytest
from shoop.apps.provides import override_provides
from shoop.core.models import Address, OrderLineType
from shoop.core.order_creator.source import OrderSource, SourceLine
from shoop.core.pricing import TaxfulPrice, TaxlessPrice
from shoop.core.taxing import TaxModule
from shoop.core.taxing.utils import stacked_value_added_taxes
from shoop.testing.factories import get_shop, get_tax


TAX_MODULE_SPEC = [__name__ + ":IrvineCaliforniaTaxation"]


class IrvineCaliforniaTaxation(TaxModule):
    identifier = "irvine"

    def get_taxed_price_for(self, context, item, price):
        taxes = []
        if context.postal_code == "92602":
            taxes = [
                # Based on data from TaxJar
                get_tax("CA", "California", rate="0.065"),
                get_tax("CA-OC", "Orange County", rate="0.01"),
                get_tax("CA-OC-IR", "Irvine", rate="0.00"),
                get_tax("CA-OC-IR-DS", "District tax", rate="0.005"),
            ]
        return stacked_value_added_taxes(price, taxes)


@pytest.mark.django_db
def test_stacked_tax_taxless_price():
    source = OrderSource(get_shop(prices_include_tax=False))
    assert source.prices_include_tax is False
    source.add_line(
        type=OrderLineType.OTHER, quantity=1, unit_price=source.create_price(10)
    )
    with override_provides("tax_module", TAX_MODULE_SPEC):
        with override_settings(SHOOP_TAX_MODULE="irvine"):
            source.shipping_address = Address(
                street="16215 Alton Pkwy",
                postal_code="92602",
            )
            line = source.get_final_lines(with_taxes=True)[0]
            assert isinstance(line, SourceLine)
            assert line.taxes
            assert line.taxful_total_price.value == Decimal("10.800")
            source.uncache()

            # Let's move out to a taxless location.
            source.shipping_address.postal_code = "11111"
            line = source.get_final_lines(with_taxes=True)[0]
            assert isinstance(line, SourceLine)
            assert not line.taxes
            assert line.taxful_total_price.value == Decimal("10")


@pytest.mark.django_db
def test_stacked_tax_taxful_price():
    shop = get_shop(prices_include_tax=True, currency='EUR')
    source = OrderSource(shop)
    assert source.prices_include_tax
    source.add_line(
        type=OrderLineType.OTHER, quantity=1, unit_price=source.create_price(20)
    )
    with override_provides("tax_module", TAX_MODULE_SPEC):
        with override_settings(SHOOP_TAX_MODULE="irvine"):
            source.shipping_address = Address(
                street="16215 Alton Pkwy",
                postal_code="92602",
            )
            line = source.get_final_lines(with_taxes=True)[0]
            assert isinstance(line, SourceLine)
            assert line.taxes
            assert line.taxful_total_price == TaxfulPrice(20, 'EUR')
            assert_almost_equal(line.taxless_total_price, TaxlessPrice("18.518518", 'EUR'))
            source.uncache()

            # Let's move out to a taxless location.
            source.shipping_address.postal_code = "11111"
            line = source.get_final_lines(with_taxes=True)[0]
            assert isinstance(line, SourceLine)
            assert not line.taxes
            assert line.taxful_total_price == TaxfulPrice(20, source.currency)
            assert line.taxless_total_price.value == Decimal("20")


def assert_almost_equal(x, y):
    assert Decimal(abs(x - y)) < 0.00001
