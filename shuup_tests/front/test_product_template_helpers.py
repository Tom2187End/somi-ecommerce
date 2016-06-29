# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import (
    ProductCrossSell, ProductCrossSellType, StockBehavior
)
from shuup.front.template_helpers import product as product_helpers
from shuup.testing.factories import (
    create_product, get_default_shop, get_default_supplier
)
from shuup_tests.front.fixtures import get_jinja_context


def _create_cross_sell_products(product, shop, supplier, type, product_count):
    for count in range(product_count):
        related_product = create_product(
            "{}-test-sku-{}".format(type, count),
            shop=shop,
            supplier=supplier,
            stock_behavior=StockBehavior.UNSTOCKED
        )
        ProductCrossSell.objects.create(product1=product, product2=related_product, type=type)


@pytest.mark.django_db
def test_cross_sell_plugin_type():
    """
    Test that template helper returns correct number of cross sells when shop contains multiple
    relation types
    """
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("test-sku", shop=shop, supplier=supplier, stock_behavior=StockBehavior.UNSTOCKED)
    context = get_jinja_context(product=product)
    type_counts = ((ProductCrossSellType.RELATED, 1),
                   (ProductCrossSellType.RECOMMENDED, 2),
                   (ProductCrossSellType.BOUGHT_WITH, 3))

    # Create cross sell products and relations in different quantities
    for type, count in type_counts:
        _create_cross_sell_products(product, shop, supplier, type, count)
        assert ProductCrossSell.objects.filter(product1=product, type=type).count() == count

    # Make sure quantities returned by plugin match
    for type, count in type_counts:
        assert len(list(product_helpers.get_product_cross_sells(context, product, type, count))) == count


@pytest.mark.django_db
def test_cross_sell_plugin_count():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("test-sku", shop=shop, supplier=supplier, stock_behavior=StockBehavior.UNSTOCKED)
    context = get_jinja_context(product=product)
    total_count = 5
    trim_count = 3

    type = ProductCrossSellType.RELATED
    _create_cross_sell_products(product, shop, supplier, type, total_count)
    assert ProductCrossSell.objects.filter(product1=product, type=type).count() == total_count

    assert len(list(product_helpers.get_product_cross_sells(context, product, type, trim_count))) == trim_count
