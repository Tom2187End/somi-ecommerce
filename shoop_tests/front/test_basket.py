# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from shoop.front.basket import get_basket
from shoop.simple_pricing.models import SimpleProductPrice
from shoop.testing.factories import get_default_shop, create_product, get_default_supplier
from shoop_tests.utils import printable_gibberish
from django.test.utils import override_settings


@pytest.mark.django_db
@pytest.mark.parametrize("storage", [
    "shoop.front.basket.storage:DirectSessionBasketStorage",
])
def test_basket(rf, storage):
    quantities = [3, 12, 44, 23, 65]
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier)
    SimpleProductPrice.objects.get_or_create(shop=shop, product=product, defaults={"price": 50, "includes_tax": False})
    with override_settings(SHOOP_BASKET_STORAGE_CLASS_SPEC=storage):
        for q in quantities:
            request = rf.get("/")
            request.session = {}
            request.shop = shop
            basket = get_basket(request)
            assert basket == request.basket
            line = basket.add_product(supplier=supplier, shop=shop, product=product, quantity=q)
            assert line.quantity == q
            assert basket.get_lines()
            assert basket.get_product_ids_and_quantities().get(product.pk) == q
            basket.save()
            delattr(request, "basket")
            basket = get_basket(request)
            assert basket.get_product_ids_and_quantities().get(product.pk) == q
