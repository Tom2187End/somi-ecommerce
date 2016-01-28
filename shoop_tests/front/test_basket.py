# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.db.models import Sum
from django.test.utils import override_settings

from shoop.front.basket import get_basket
from shoop.front.models import StoredBasket
from shoop.testing.factories import (
    create_product, get_default_shop, get_default_supplier
)
from shoop.testing.utils import apply_request_middleware
from shoop_tests.utils import printable_gibberish


@pytest.mark.django_db
@pytest.mark.parametrize("storage", [
    "shoop.front.basket.storage:DirectSessionBasketStorage",
    "shoop.front.basket.storage:DatabaseBasketStorage",
])
def test_basket(rf, storage):
    StoredBasket.objects.all().delete()
    quantities = [3, 12, 44, 23, 65]
    shop = get_default_shop()
    supplier = get_default_supplier()
    products_and_quantities = []
    for quantity in quantities:
        product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
        products_and_quantities.append((product, quantity))

    is_database = (storage == "shoop.front.basket.storage:DatabaseBasketStorage")
    with override_settings(SHOOP_BASKET_STORAGE_CLASS_SPEC=storage):
        for product, q in products_and_quantities:
            request = rf.get("/")
            request.session = {}
            request.shop = shop
            apply_request_middleware(request)
            basket = get_basket(request)
            assert basket == request.basket
            assert basket.product_count == 0
            line = basket.add_product(supplier=supplier, shop=shop, product=product, quantity=q)
            assert line.quantity == q
            assert basket.get_lines()
            assert basket.get_product_ids_and_quantities().get(product.pk) == q
            assert basket.product_count == q
            basket.save()
            delattr(request, "basket")
            basket = get_basket(request)
            assert basket.get_product_ids_and_quantities().get(product.pk) == q
            if is_database:
                product_ids = set(StoredBasket.objects.last().products.values_list("id", flat=True))
                assert product_ids == set([product.pk])

        if is_database:
            stats = StoredBasket.objects.all().aggregate(
                n=Sum("product_count"),
                tfs=Sum("taxful_total_price_value"),
                tls=Sum("taxless_total_price_value"),
            )
            assert stats["n"] == sum(quantities)
            if shop.prices_include_tax:
                assert stats["tfs"] == sum(quantities) * 50
            else:
                assert stats["tls"] == sum(quantities) * 50


@pytest.mark.django_db
def test_basket_dirtying_with_fnl(rf):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
    request = rf.get("/")
    request.session = {}
    request.shop = shop
    apply_request_middleware(request)
    basket = get_basket(request)
    line = basket.add_product(
        supplier=supplier,
        shop=shop,
        product=product,
        quantity=1,
        force_new_line=True,
        extra={"foo": "foo"}
    )
    assert basket.dirty  # The change should have dirtied the basket
