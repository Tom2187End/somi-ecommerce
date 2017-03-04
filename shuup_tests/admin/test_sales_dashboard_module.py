# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from datetime import date

import pytest
from bs4 import BeautifulSoup

from shuup.admin.modules.sales_dashboard.dashboard import (
    get_recent_orders_block, get_shop_overview_block,
    OrderValueChartDashboardBlock
)
from shuup.core.models import OrderStatus
from shuup.testing.factories import (
    create_product, create_random_order, create_random_person,
    DEFAULT_CURRENCY, get_default_product, get_default_shop
)

NUM_ORDERS_COLUMN_INDEX = 2
NUM_CUSTOMERS_COLUMN_INDEX = 3


def get_order_for_date(dt, product):
    order = create_random_order(customer=create_random_person(), products=[product])
    order.order_date = dt
    order.status = OrderStatus.objects.get_default_complete()
    order.save()
    return order

@pytest.mark.django_db
def test_order_chart_works():
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    chart = OrderValueChartDashboardBlock("test", order.currency).get_chart()
    assert len(chart.datasets[0]) > 0


@pytest.mark.django_db
@pytest.mark.parametrize("data", [
    # date, today, mtd, ytd
    (date(1976, 3, 6), 2, 3, 4),
    (date(2005, 9, 15), 2, 3, 4),
    (date(2012, 7, 1), 3, 3, 4),
    (date(2016, 1, 1), 4, 4, 4),
    (date(2016, 12, 31), 2, 3, 4),
    (date(2020, 2, 29), 2, 3, 4),
])
def test_shop_overview_block(rf, data):
    (today, expected_today, expected_mtd, expected_ytd) = data
    product = get_default_product()
    sp = product.get_shop_instance(get_default_shop())
    sp.default_price_value = "10"
    sp.save()
    get_order_for_date(today, product)
    o = get_order_for_date(today, product)
    o.customer = None
    o.save()
    get_order_for_date(date(today.year - 1, 12, 31), product)
    get_order_for_date(date(today.year, 1, 1), product)
    get_order_for_date(date(today.year, today.month, 1), product)

    block = get_shop_overview_block(rf.get("/"), DEFAULT_CURRENCY, today)
    soup = BeautifulSoup(block.content)
    _, today_sales, mtd, ytd, totals = soup.find_all("tr")

    assert today_sales.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == str(expected_today)
    assert today_sales.find_all("td")[NUM_CUSTOMERS_COLUMN_INDEX].string == str(expected_today)
    assert mtd.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == str(expected_mtd)
    assert mtd.find_all("td")[NUM_CUSTOMERS_COLUMN_INDEX].string == str(expected_mtd)
    assert ytd.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == str(expected_ytd)
    assert ytd.find_all("td")[NUM_CUSTOMERS_COLUMN_INDEX].string == str(expected_ytd)
    assert totals.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == "5"
    assert totals.find_all("td")[NUM_CUSTOMERS_COLUMN_INDEX].string == "5"


@pytest.mark.django_db
def test_recent_orders_block(rf):
    order = create_random_order(customer=create_random_person(), products=[get_default_product()])
    block = get_recent_orders_block(rf.get("/"), DEFAULT_CURRENCY)
    assert order.customer.name in block.content
