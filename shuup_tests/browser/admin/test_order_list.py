# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest
from django.core.urlresolvers import reverse

from shuup.core.models import Order, OrderStatus
from shuup.testing.browser_utils import (
    click_element, wait_until_appeared, wait_until_condition
)
from shuup.testing.factories import create_empty_order, get_default_shop
from shuup.testing.utils import initialize_admin_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_orders_list_view(browser, admin_user, live_server, settings):
    shop = get_default_shop()
    for i in range(0, 10):
        order = create_empty_order(shop=shop)
        order.save()

    # Set last one canceled
    Order.objects.last().set_canceled()

    initialize_admin_browser_test(browser, live_server, settings)
    _visit_orders_list_view(browser, live_server)
    _test_status_filter(browser)  # Will set three orders from end canceled


def _visit_orders_list_view(browser, live_server):
    url = reverse("shuup_admin:order.list")
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, condition=lambda x: x.is_text_present("Orders"))
    wait_until_appeared(browser, ".picotable-item-info")


def _test_status_filter(browser):
    # Check initial row count where the cancelled order should be excluded
    _check_row_count(browser, Order.objects.count() - 1)

    # Take three last valid orders and set those cancelled
    orders = Order.objects.valid()[:3]
    for order in orders:
        order.set_canceled()

    # Filter with cancelled
    cancelled_status = OrderStatus.objects.get_default_canceled()
    _change_status_filter(browser, "%s" % cancelled_status.pk)

    # Check cancelled row count
    _check_row_count(browser, (3 + 1))

    # Filter with initial
    initial_status = OrderStatus.objects.get_default_initial()
    _change_status_filter(browser, "%s" % initial_status.pk)

    # Take new count
    _check_row_count(browser, (Order.objects.count() - 3 - 1))

    # Change status filter to all
    _change_status_filter(browser, '"_all"')

    # Now all orders should be visible
    _check_row_count(browser, Order.objects.count())


def _check_row_count(browser, expected_row_count):
    picotable = browser.find_by_id("picotable")
    tbody = picotable.find_by_tag("tbody").first
    wait_until_condition(browser, lambda x: len(x.find_by_css("#picotable tbody tr")) == expected_row_count)
    # technically this is handled above, but do the assertion anyways ;)
    assert len(browser.find_by_css("#picotable tbody tr")) == expected_row_count


def _change_status_filter(browser, to_value):
    picotable = browser.find_by_id("picotable")
    click_element(browser, "#picotable div.choice-filter")
    click_element(browser, "#picotable div.choice-filter option[value='%s']" % to_value)
