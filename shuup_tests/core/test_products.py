# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from shuup.core.models import (
    AnonymousContact, get_person_contact, Product, ProductVisibility,
    ShopProductVisibility
)
from shuup.testing.factories import (
    create_product, get_default_customer_group, get_default_shop,
    get_default_shop_product
)
from shuup_tests.core.utils import modify
from shuup_tests.utils.fixtures import regular_user


@pytest.mark.parametrize("visibility,show_in_list,show_in_search", [
    (ShopProductVisibility.NOT_VISIBLE, False, False),
    (ShopProductVisibility.SEARCHABLE, False, True),
    (ShopProductVisibility.LISTED, True, False),
    (ShopProductVisibility.ALWAYS_VISIBLE, True, True),
])
@pytest.mark.django_db
def test_product_query(visibility, show_in_list, show_in_search, admin_user, regular_user):
    shop = get_default_shop()
    product = create_product("test-sku", shop=shop)
    shop_product = product.get_shop_instance(shop)
    anon_contact = AnonymousContact()
    regular_contact = get_person_contact(regular_user)
    admin_contact = get_person_contact(admin_user)

    shop_product.visibility = visibility
    shop_product.save()

    assert shop_product.visibility_limit == ProductVisibility.VISIBLE_TO_ALL

    # Anonymous contact should be the same as no contact
    assert (product in Product.objects.listed(shop=shop)) == show_in_list
    assert (product in Product.objects.searchable(shop=shop)) == show_in_search
    assert (product in Product.objects.listed(shop=shop, customer=anon_contact)) == show_in_list
    assert (product in Product.objects.searchable(shop=shop, customer=anon_contact)) == show_in_search

    # Admin should see all non-deleted results
    assert product in Product.objects.listed(shop=shop, customer=admin_contact)
    assert product in Product.objects.searchable(shop=shop, customer=admin_contact)

    # Anonymous contact shouldn't see products with logged in visibility limit
    shop_product.visibility_limit = ProductVisibility.VISIBLE_TO_LOGGED_IN
    shop_product.save()
    assert product not in Product.objects.listed(shop=shop, customer=anon_contact)
    assert product not in Product.objects.searchable(shop=shop, customer=anon_contact)

    # Reset visibility limit
    shop_product.visibility_limit = ProductVisibility.VISIBLE_TO_ALL
    shop_product.save()

    # No one should see deleted products
    product.soft_delete()
    assert product not in Product.objects.listed(shop=shop)
    assert product not in Product.objects.searchable(shop=shop)
    assert product not in Product.objects.listed(shop=shop, customer=admin_contact)
    assert product not in Product.objects.searchable(shop=shop, customer=admin_contact)


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_product_query_with_group_visibility(regular_user):
    default_group = get_default_customer_group()
    shop_product = get_default_shop_product()
    shop_product.visibility_limit = 3
    shop_product.save()
    shop = shop_product.shop
    product = shop_product.product
    shop_product.visibility_groups.add(default_group)
    regular_contact = get_person_contact(regular_user)

    assert not Product.objects.listed(shop=shop, customer=regular_contact).filter(pk=product.pk).exists()
    regular_contact.groups.add(default_group)
    assert Product.objects.listed(shop=shop, customer=regular_contact).filter(pk=product.pk).count() == 1

    shop_product.visibility_groups.add(regular_contact.get_default_group())
    # Multiple visibility groups for shop product shouldn't cause duplicate matches
    assert Product.objects.listed(shop=shop, customer=regular_contact).filter(pk=product.pk).count() == 1
