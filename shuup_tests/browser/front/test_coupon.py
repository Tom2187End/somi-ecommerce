# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest

from django.core.urlresolvers import reverse
from django.utils.translation import activate

from shuup.campaigns.models import BasketCampaign, Coupon
from shuup.campaigns.models.basket_conditions import (
    CategoryProductsBasketCondition
)
from shuup.campaigns.models.basket_effects import (
    BasketDiscountPercentage
)
from shuup.core import cache
from shuup.core.models import (
    Category, CategoryStatus, Manufacturer, Product, ProductMode,
    ProductVariationVariable, ProductVariationVariableValue, ShopProduct
)
from shuup.front.utils.sorts_and_filters import (
    set_configuration
)
from shuup.testing.browser_utils import (
    click_element, move_to_element, wait_until_appeared, wait_until_condition,
    wait_until_disappeared
)
from shuup.testing.factories import (
    create_product, get_default_payment_method, get_default_shipping_method,
    get_default_shop, get_default_supplier
)
from shuup.testing.utils import initialize_front_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


CATEGORY_DATA = [
    ("First Category", "cat-1"),
]

CATEGORY_PRODUCT_DATA = [
    ("Test Product", "test-sku-1", 123),
    ("A Test Product", "test-sku-2", 720),
    ("XTest Product", "test-sku-3", 1),
]


@pytest.mark.browser
@pytest.mark.djangodb
def test_category_product_list(browser, live_server, settings):
    activate("en")
    # initialize
    cache.clear()
    shop = get_default_shop()
    get_default_payment_method()
    get_default_shipping_method()

    first_category = Category.objects.create(
        identifier="cat-1", status=CategoryStatus.VISIBLE, name="First Category")
    first_category.shops.add(shop)

    _populate_products_form_data(CATEGORY_PRODUCT_DATA, shop, first_category)

    # initialize test and go to front page
    browser = initialize_front_browser_test(browser, live_server)

    _add_product_to_basket_from_category(live_server, browser, first_category, shop)
    _activate_basket_campaign_through_coupon(browser, first_category, shop)


def _populate_products_form_data(data, shop, category=None):
    for name, sku, price in data:
        product = _create_orderable_product(name, sku, price=price)
        shop_product = product.get_shop_instance(shop)
        shop_product.primary_category = category
        shop_product.save()
        if category:
            shop_product.categories.add(category)


def _create_orderable_product(name, sku, price):
    supplier = get_default_supplier()
    shop = get_default_shop()
    product = create_product(sku=sku, shop=shop, supplier=supplier, default_price=price, name=name)
    return product


def _add_product_to_basket_from_category(live_server, browser, first_category, shop):
    url = reverse("shuup:category", kwargs={"pk": first_category.pk, "slug": first_category.slug})
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_text_present(first_category.name))

    # Make sure that the correct price is visible
    product = Product.objects.filter(sku="test-sku-2").first()
    selector = "#product-%s div.price-line span.lead strong" % product.id
    wait_until_condition(browser, lambda x: "720" in x.find_by_css(selector).first.text)

    # Test product price update
    new_price = 42
    shop_product = product.get_shop_instance(shop)
    shop_product.default_price_value = new_price
    shop_product.save()

    browser.reload()
    wait_until_condition(browser, lambda x: str(new_price) in x.find_by_css(selector).first.text)

    # Go to product detail and update the price one more time
    click_element(browser, selector)

    product_detail_price_selector = "#product-price-div-%s span.product-price strong" % product.id
    wait_until_condition(browser, lambda x: str(new_price) in x.find_by_css(product_detail_price_selector).first.text)

    last_price = 120.53
    shop_product = product.get_shop_instance(shop)
    shop_product.default_price_value = last_price
    shop_product.save()

    browser.reload()
    wait_until_condition(browser, lambda x: str(last_price) in x.find_by_css(product_detail_price_selector).first.text)

    # Add product to basket and navigate to basket view
    click_element(browser, "#add-to-cart-button-%s" % product.pk)  # add product to basket
    wait_until_appeared(browser, ".cover-wrap")
    wait_until_disappeared(browser, ".cover-wrap")
    click_element(browser, "#navigation-basket-partial")  # open upper basket navigation menu
    click_element(browser, "a[href='/basket/']")  # click the link to basket in dropdown
    wait_until_condition(browser, lambda x: x.is_text_present("Shopping cart"))  # we are in basket page
    wait_until_condition(browser, lambda x: x.is_text_present(product.name))  # product is in basket


def _activate_basket_campaign_through_coupon(browser, category, shop):
    # We should already be at basket so let's verify the total
    wait_until_condition(browser, lambda x: "120.53" in x.find_by_css("div.total-price h2").first.text)

    coupon_code = _create_campaign(category, shop)
    click_element(browser, "a[class='coupon-toggler']")
    browser.fill("code", coupon_code)
    click_element(browser, "#submit-code")

    wait_until_condition(browser, lambda x: x.is_text_present(coupon_code))
    wait_until_condition(browser, lambda x: "-€24.11" in x.find_by_css("div.product-sum h4.price").last.text)
    wait_until_condition(browser, lambda x: "€96.42" in x.find_by_css("div.total-price h2").first.text)


def _create_campaign(category, shop):
    basket_condition = CategoryProductsBasketCondition.objects.create(quantity=1)
    basket_condition.categories.add(category)

    coupon = Coupon.objects.create(code="couponcode", active=True)

    campaign = BasketCampaign.objects.create(
        shop=shop, public_name="test", name="test", active=True, coupon=coupon
    )
    campaign.conditions.add(basket_condition)
    campaign.save()

    BasketDiscountPercentage.objects.create(campaign=campaign, discount_percentage="0.20")

    return coupon.code
