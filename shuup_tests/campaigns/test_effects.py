# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

import pytest

from shuup.campaigns.models import BasketCampaign, Coupon, CatalogCampaign
from shuup.campaigns.models.catalog_filters import ProductFilter
from shuup.campaigns.models.product_effects import ProductDiscountAmount, ProductDiscountPercentage
from shuup.campaigns.models.basket_conditions import (
    BasketTotalProductAmountCondition, ProductsInBasketCondition
)
from shuup.campaigns.models.basket_effects import (
    BasketDiscountAmount, BasketDiscountPercentage
)
from shuup.campaigns.models.basket_line_effects import (
    DiscountFromCategoryProducts, DiscountFromProduct, FreeProductLine
)
from shuup.core.models import OrderLineType, ShopProduct
from shuup.core.order_creator._source import LineSource
from shuup.front.basket import get_basket
from shuup.testing.factories import (
    CategoryFactory, create_product, get_default_supplier, get_shipping_method
)
from shuup_tests.campaigns import initialize_test
from shuup_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_basket_free_product(rf):
    request, shop, _ = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier()

    single_product_price = "50"
    original_quantity = 2
     # create basket rule that requires 2 products in basket
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=2)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    second_product = create_product(printable_gibberish(),
                                    shop=shop,
                                    supplier=supplier,
                                    default_price=single_product_price)

    rule = BasketTotalProductAmountCondition.objects.create(value="2")

    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test")
    campaign.conditions.add(rule)

    effect = FreeProductLine.objects.create(campaign=campaign, quantity=2)
    effect.products.add(second_product)

    basket.uncache()
    final_lines = basket.get_final_lines()

    assert len(final_lines) == 3

    line_types = [l.type for l in final_lines]
    assert OrderLineType.DISCOUNT not in line_types

    for line in basket.get_final_lines():
        assert line.type in [OrderLineType.PRODUCT, OrderLineType.SHIPPING]
        if line.type == OrderLineType.SHIPPING:
            continue
        if line.product != product:
            assert line.product == second_product
            assert line.line_source == LineSource.DISCOUNT_MODULE
            assert line.quantity == original_quantity
        else:
            assert line.line_source == LineSource.CUSTOMER


@pytest.mark.django_db
def test_basket_free_product_coupon(rf):
    request, shop, _ = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier()

    single_product_price = "50"
    discount_amount_value = "10"

     # create basket rule that requires 2 products in basket
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    second_product = create_product(printable_gibberish(),
                                    shop=shop,
                                    supplier=supplier,
                                    default_price=single_product_price)

    rule = BasketTotalProductAmountCondition.objects.create(value="2")
    coupon = Coupon.objects.create(code="TEST", active=True)

    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test", coupon=coupon)
    campaign.conditions.add(rule)

    effect = FreeProductLine.objects.create(campaign=campaign)
    effect.products.add(second_product)

    basket.add_code(coupon.code)

    basket.uncache()
    final_lines = basket.get_final_lines()

    assert len(final_lines) == 3

    line_types = [l.type for l in final_lines]
    assert OrderLineType.DISCOUNT not in line_types

    for line in basket.get_final_lines():
        assert line.type in [OrderLineType.PRODUCT, OrderLineType.SHIPPING]
        if line.type == OrderLineType.SHIPPING:
            continue

        if line.product != product:
            assert line.product == second_product


@pytest.mark.django_db
def test_productdiscountamount(rf):
    # Buy X amount of Y get Z discount from Y
    request, shop, _ = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier()

    single_product_price = "50"
    discount_amount_value = "10"
    quantity = 2

     # create basket rule that requires 2 products in basket
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=quantity)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    rule = ProductsInBasketCondition.objects.create(quantity=2)
    rule.products.add(product)
    rule.save()

    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test")
    campaign.conditions.add(rule)

    effect = DiscountFromProduct.objects.create(
        campaign=campaign, discount_amount=discount_amount_value)
    effect.products.add(product)

    assert rule.matches(basket, [])
    basket.uncache()

    final_lines = basket.get_final_lines()

    assert len(final_lines) == 2  # no new lines since the effect touches original lines
    expected_discount_amount = basket.create_price(discount_amount_value)
    original_price = basket.create_price(single_product_price) * quantity
    line = final_lines[0]
    assert line.discount_amount == expected_discount_amount
    assert basket.total_price == original_price - expected_discount_amount



@pytest.mark.django_db
def test_productdiscountamount_greater_then_products(rf):
    # Buy X amount of Y get Z discount from Y
    request, shop, _ = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier()

    single_product_price = "50"
    discount_amount_value = "150"
    quantity = 2

    # the expected discount amount should not be greater than the products
    expected_discount_amount = basket.create_price(single_product_price) * quantity

     # create basket rule that requires 2 products in basket
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=quantity)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    rule = ProductsInBasketCondition.objects.create(quantity=2)
    rule.products.add(product)
    rule.save()

    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test")
    campaign.conditions.add(rule)

    effect = DiscountFromProduct.objects.create(
        campaign=campaign, discount_amount=discount_amount_value)
    effect.products.add(product)

    assert rule.matches(basket, [])
    basket.uncache()

    final_lines = basket.get_final_lines()

    assert len(final_lines) == 2  # no new lines since the effect touches original lines

    original_price = basket.create_price(single_product_price) * quantity
    line = final_lines[0]
    assert line.discount_amount == expected_discount_amount
    assert basket.total_price == original_price - expected_discount_amount


@pytest.mark.parametrize("include_tax", (True, False))
@pytest.mark.django_db
def test_product_category_discount_amount_greater_then_products(rf, include_tax):
    # Buy X amount of Y get Z discount from Y
    request, shop, _ = initialize_test(rf, include_tax)

    basket = get_basket(request)
    supplier = get_default_supplier()

    single_product_price = "50"
    discount_amount_value = "150"
    quantity = 2

    # the expected discount amount should not be greater than the products
    expected_discount_amount = basket.create_price(single_product_price) * quantity

    category = CategoryFactory()

     # create basket rule that requires 2 products in basket
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
    ShopProduct.objects.get(shop=shop, product=product).categories.add(category)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=quantity)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    rule = ProductsInBasketCondition.objects.create(quantity=2)
    rule.products.add(product)
    rule.save()

    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test")
    campaign.conditions.add(rule)

    DiscountFromCategoryProducts.objects.create(campaign=campaign,
                                                discount_amount=discount_amount_value,
                                                category=category)
    assert rule.matches(basket, [])
    basket.uncache()

    final_lines = basket.get_final_lines()

    assert len(final_lines) == 2  # no new lines since the effect touches original lines

    original_price = basket.create_price(single_product_price) * quantity
    line = final_lines[0]
    assert line.discount_amount == expected_discount_amount
    assert basket.total_price == original_price - expected_discount_amount


@pytest.mark.parametrize("include_tax", (True, False))
@pytest.mark.django_db
def test_product_category_discount_percentage_greater_then_products(rf, include_tax):
    # Buy X amount of Y get Z discount from Y
    request, shop, _ = initialize_test(rf, include_tax)

    basket = get_basket(request)
    supplier = get_default_supplier()

    single_product_price = "50"
    discount_percentage = Decimal(1.9) # 190%
    quantity = 2

    # the expected discount amount should not be greater than the products
    expected_discount_amount = basket.create_price(single_product_price) * quantity

    category = CategoryFactory()

     # create basket rule that requires 2 products in basket
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
    ShopProduct.objects.get(shop=shop, product=product).categories.add(category)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=quantity)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    rule = ProductsInBasketCondition.objects.create(quantity=2)
    rule.products.add(product)
    rule.save()

    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test")
    campaign.conditions.add(rule)

    DiscountFromCategoryProducts.objects.create(campaign=campaign,
                                                discount_percentage=discount_percentage,
                                                category=category)
    assert rule.matches(basket, [])
    basket.uncache()

    final_lines = basket.get_final_lines()

    assert len(final_lines) == 2  # no new lines since the effect touches original lines

    original_price = basket.create_price(single_product_price) * quantity
    line = final_lines[0]
    assert line.discount_amount == expected_discount_amount
    assert basket.total_price == original_price - expected_discount_amount



@pytest.mark.parametrize("include_tax", (True, False))
@pytest.mark.django_db
def test_discount_no_limits(rf, include_tax):
    # check whether is it possible to earn money buying from us
    # adding lots of effects
    request, shop, _ = initialize_test(rf, include_tax)

    basket = get_basket(request)
    supplier = get_default_supplier()

    single_product_price = Decimal(50)
    quantity = 4
    discount_amount = (single_product_price * quantity * 2)
    discount_percentage = Decimal(1.9) # 190%

    second_product = create_product(printable_gibberish(),
                                    shop=shop,
                                    supplier=supplier,
                                    default_price=single_product_price)

    # the expected discount amount should not be greater than the products
    expected_discount_amount = basket.create_price(single_product_price) * quantity

    category = CategoryFactory()

     # create basket rule that requires 2 products in basket
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
    ShopProduct.objects.get(shop=shop, product=product).categories.add(category)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=quantity)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    rule = ProductsInBasketCondition.objects.create(quantity=2)
    rule.products.add(product)
    rule.save()

    # BasketCampaign
    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test")
    campaign.conditions.add(rule)

    # effect 1 - categories from products
    DiscountFromCategoryProducts.objects.create(campaign=campaign,
                                                discount_percentage=discount_percentage,
                                                category=category)

    # effect 2 - discount from products
    effect2 = DiscountFromProduct.objects.create(campaign=campaign, discount_amount=discount_amount)
    effect2.products.add(product)

    # effect 3 - basket discount
    BasketDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount)

    # effect 4 - basket discount percetage
    BasketDiscountPercentage.objects.create(campaign=campaign, discount_percentage=discount_percentage)

    basket.uncache()

    final_lines = basket.get_final_lines()
    assert len(final_lines) == 3

    original_price = basket.create_price(single_product_price) * quantity
    line = final_lines[0]
    assert line.discount_amount == expected_discount_amount
    assert basket.total_price == original_price - expected_discount_amount

    # effect free - aaaww yes, it's free
    effect_free = FreeProductLine.objects.create(campaign=campaign, quantity=1)
    effect_free.products.add(second_product)

    basket.uncache()

    final_lines = basket.get_final_lines()
    assert len(final_lines) == 4
    line = final_lines[0]
    assert line.discount_amount == expected_discount_amount
    assert basket.total_price == original_price - expected_discount_amount

    # CatalogCampaign
    catalog_campaign = CatalogCampaign.objects.create(active=True, shop=shop, name="test2", public_name="test")
    product_filter = ProductFilter.objects.create()
    product_filter.products.add(product)
    catalog_campaign.filters.add(product_filter)

    # effect 5 - ProductDiscountAmount
    ProductDiscountAmount.objects.create(campaign=catalog_campaign, discount_amount=discount_amount)

    # effct 6 - ProductDiscountPercentage
    ProductDiscountPercentage.objects.create(campaign=catalog_campaign, discount_percentage=discount_percentage)

    basket.uncache()

    final_lines = basket.get_final_lines()
    assert len(final_lines) == 4
    line = final_lines[0]
    assert line.discount_amount == expected_discount_amount
    assert basket.total_price == original_price - expected_discount_amount
