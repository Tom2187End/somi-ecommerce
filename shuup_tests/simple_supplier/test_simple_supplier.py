# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import pytest
import random

from shuup.admin.modules.products.views.edit import ProductEditView
from shuup.core.models import StockBehavior, Supplier
from shuup.simple_supplier.admin_module.forms import SimpleSupplierForm
from shuup.simple_supplier.admin_module.views import process_stock_adjustment

from shuup.testing.factories import (
    create_order_with_product, create_product, get_default_shop
)
from shuup_tests.simple_supplier.utils import get_simple_supplier


@pytest.mark.django_db
def test_simple_supplier(rf):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop)
    ss = supplier.get_stock_status(product.pk)
    assert ss.product == product
    assert ss.logical_count == 0
    num = random.randint(100, 500)
    supplier.adjust_stock(product.pk, +num)
    assert supplier.get_stock_status(product.pk).logical_count == num
    # Create order ...
    order = create_order_with_product(product, supplier, 10, 3, shop=shop)
    quantities = order.get_product_ids_and_quantities()
    pss = supplier.get_stock_status(product.pk)
    assert pss.logical_count == (num - quantities[product.pk])
    assert pss.physical_count == num
    # Create shipment ...
    order.create_shipment_of_all_products(supplier)
    pss = supplier.get_stock_status(product.pk)
    assert pss.physical_count == (num - quantities[product.pk])
    # Cancel order...
    order.set_canceled()
    pss = supplier.get_stock_status(product.pk)
    assert pss.logical_count == (num)


@pytest.mark.django_db
def test_supplier_with_stock_counts(rf):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop, supplier)
    quantity = random.randint(100, 600)
    supplier.adjust_stock(product.pk, quantity)
    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == quantity
    # No orderability errors since product is not stocked
    assert not list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity+1, customer=None))

    product.stock_behavior = StockBehavior.STOCKED  # Make product stocked
    product.save()

    assert not list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity, customer=None))
    # Now since product is stocked we get orderability error with quantity + 1
    assert list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity+1, customer=None))


@pytest.mark.django_db
def test_supplier_with_stock_counts(rf, admin_user):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop, supplier)
    quantity = random.randint(100, 600)
    supplier.adjust_stock(product.pk, quantity)
    adjust_quantity = random.randint(100, 600)
    request = rf.get("/")
    request.user = admin_user
    request.POST = {
        "purchase_price": decimal.Decimal(32.00),
        "delta": adjust_quantity
    }
    response = process_stock_adjustment(request, supplier.id, product.id)
    assert response.status_code == 400  # Only POST is allowed
    request.method = "POST"
    response = process_stock_adjustment(request, supplier.id, product.id)
    assert response.status_code == 200
    pss = supplier.get_stock_status(product.pk)
    # Product stock values should be adjusted
    assert pss.logical_count == (quantity + adjust_quantity)


@pytest.mark.django_db
def test_admin_form(rf, admin_user):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop, supplier)
    request = rf.get("/")
    request.user = admin_user
    frm = SimpleSupplierForm(product=product, request=request)
    # Form contains 1 product even if the product is not stocked
    assert len(frm.products) == 1
    assert not frm.products[0].is_stocked()

    product.stock_behavior = StockBehavior.STOCKED  # Make product stocked
    product.save()

    # Now since product is stocked it should be in the form
    frm = SimpleSupplierForm(product=product, request=request)
    assert len(frm.products) == 1

    # Add stocked children for product
    child_product = create_product("child-test-product", shop, supplier)
    child_product.stock_behavior = StockBehavior.STOCKED
    child_product.save()
    child_product.link_to_parent(product)

    # Admin form should now contain only child products for product
    frm = SimpleSupplierForm(product=product, request=request)
    assert len(frm.products) == 1
    assert frm.products[0] == child_product


@pytest.mark.django_db
def test_new_product_admin_form_renders(rf, client, admin_user):
    """
    Make sure that no exceptions are raised when creating a new product
    with simple supplier enabled
    """
    request = rf.get("/")
    request.user = admin_user
    request.session = client.session
    view = ProductEditView.as_view()
    shop = get_default_shop()
    supplier = get_simple_supplier()
    supplier.stock_managed = True
    supplier.save()

    # This should not raise an exception
    view(request).render()

    supplier.stock_managed = False
    supplier.save()

    # Nor should this
    view(request).render()
