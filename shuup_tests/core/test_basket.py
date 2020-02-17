# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test.utils import override_settings

from shuup.core.basket import get_basket
from shuup.core.models import get_person_contact, OrderLineType
from shuup.utils.importing import cached_load
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware

CORE_BASKET_SETTINGS = dict(
    SHUUP_BASKET_ORDER_CREATOR_SPEC="shuup.core.basket.order_creator:BasketOrderCreator",
    SHUUP_BASKET_STORAGE_CLASS_SPEC="shuup.core.basket.storage:DatabaseBasketStorage",
    SHUUP_BASKET_CLASS_SPEC="shuup.core.basket.objects:Basket"
)

@pytest.mark.django_db
def test_set_customer_with_custom_basket_lines(rf):
    """
    Set anonymous to the basket customer
    """
    with override_settings(**CORE_BASKET_SETTINGS):
        factories.get_default_shop()
        user = factories.create_random_user()
        request = apply_request_middleware(rf.get("/"), user=user)
        basket = get_basket(request, "basket")
        shipping_method = factories.get_default_shipping_method()
        payment_method = factories.get_default_payment_method()
        customer = get_person_contact(user)
        customer_comment = "Some comment"

        base_unit_price = basket.shop.create_price("10.99")

        basket.add_line(
            text="Custom Line",
            type=OrderLineType.OTHER,
            line_id="random-you-know",
            shop=basket.shop,
            quantity=1,
            base_unit_price=base_unit_price,
            extra={"this is purely extra": "oh is it"}
        )

        basket.customer = customer
        assert basket.customer_comment is None
        basket.customer_comment = customer_comment
        assert basket.payment_method is None
        assert basket.shipping_method is None
        basket.payment_method = payment_method
        basket.shipping_method = shipping_method
        basket.refresh_lines()
        basket.save()
        assert basket.customer == get_person_contact(user)
        assert basket.customer_comment == "Some comment"
        assert basket.shipping_method == shipping_method
        assert basket.payment_method == payment_method
        assert len(basket.get_lines()) == 1
        assert basket.get_lines()[0].data["extra"]["this is purely extra"] == "oh is it"


@pytest.mark.django_db
def test_basket_with_custom_shop(rf):
    """
    Set a different shop for basket
    """
    with override_settings(**CORE_BASKET_SETTINGS):
        shop1 = factories.get_default_shop()
        shop2 = factories.get_shop(identifier="shop2")
        user = factories.create_random_user()
        request = apply_request_middleware(rf.get("/"), user=user, shop=shop1)
        basket_class = cached_load("SHUUP_BASKET_CLASS_SPEC")
        basket = basket_class(request, "basket", shop=shop2)
        assert basket.shop == shop2

        product_shop2 = factories.create_product("product_shop2", shop2, factories.get_default_supplier(), 10)
        line = basket.add_product(factories.get_default_supplier(), shop2, product_shop2, 1)
        assert line.shop == shop2
