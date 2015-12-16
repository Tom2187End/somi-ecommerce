import pytest

from shoop.core.pricing import TaxfulPrice, TaxlessPrice
from shoop.testing.factories import (
    create_product, get_default_product, get_default_shop
)


def init_test(request, shop, prices):
    parent = create_product("parent_product", shop=shop)
    children = [create_product("child-%d" % price, shop=shop, default_price=price) for price in prices]
    for child in children:
        child.link_to_parent(parent)
    return parent

@pytest.mark.django_db
def test_simple_product_works(rf):
    product = get_default_product()
    request = rf.get("/")
    assert product.get_child_price_range(request) == (None, None)
    assert product.get_cheapest_child_price_info(request) is None
    assert product.get_cheapest_child_price(request) is None


@pytest.mark.django_db
def test_cheapest_price_found(rf):
    prices = [100,20,50,80,90]

    shop = get_default_shop()
    request = rf.get("/")
    request.shop = shop
    parent = init_test(request, shop, prices)

    price = shop.create_price
    assert parent.get_cheapest_child_price(request) == price(min(prices))

    price_info = parent.get_cheapest_child_price_info(request)
    assert price_info.price == price(min(prices))


@pytest.mark.django_db
def test_correct_range_found(rf):
    prices = [100,20,50,80,90]

    shop = get_default_shop()
    request = rf.get("/")
    request.shop = shop
    parent = init_test(request, shop, prices)

    price = shop.create_price
    assert parent.get_child_price_range(request) == (price(min(prices)), price(max(prices)))


@pytest.mark.django_db
def test_only_one_variation_child(rf):
    prices = [20]

    shop = get_default_shop()
    request = rf.get("/")
    request.shop = shop
    parent = init_test(request, shop, prices)

    price_info = parent.get_cheapest_child_price_info(request)

    price = shop.create_price

    assert parent.get_cheapest_child_price(request) == price(min(prices))
    assert parent.get_child_price_range(request) == (price(min(prices)), price(max(prices)))
    assert price_info.price == price(min(prices))
