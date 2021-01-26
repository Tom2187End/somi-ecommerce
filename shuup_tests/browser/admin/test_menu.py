# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest
import selenium

from shuup.utils.django_compat import reverse

from shuup.testing.browser_utils import wait_until_condition, wait_until_appeared
from shuup.testing.factories import get_default_shop
from shuup.testing.browser_utils import initialize_admin_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_TRAVIS", "0") == "1", reason="Disable when run through tox.")
def test_menu(browser, admin_user, live_server, settings):
    get_default_shop()
    initialize_admin_browser_test(browser, live_server, settings)

    wait_until_condition(browser, lambda x: x.is_text_present("Welcome!"))
    wait_until_condition(browser, lambda x: x.is_text_present("Quicklinks"))

    try:
        browser.find_by_css(".quicklinks a").first.click()
    except selenium.common.exceptions.TimeoutException as e:
        # TODO: Revise!
        # Give the Quicklinks click second chance. It seems there is a way
        # to click it too fast. Wouldn't be too worried this to be actual
        # issue with the menu. Looks like something that happens under
        # 10% of time in my local environment, but main reason for this
        # is Travis.
        browser.find_by_css(".quicklinks a").first.click()


    wait_until_appeared(browser, ".item-category.item-active")
    browser.find_by_css(".menu-list li a")[2].click()

    wait_until_condition(browser, lambda x: x.is_text_present("New shop product"))


@pytest.mark.browser
@pytest.mark.djangodb
def test_menu_small_device(browser, admin_user, live_server, settings):
    get_default_shop()

    browser.driver.set_window_size(480, 960)
    initialize_admin_browser_test(browser, live_server, settings)

    # Lets navigate to orders so we don't click that menu button too fast
    # it seems that without this we click the menu button before the
    # page is actually ready.
    url = reverse("shuup_admin:order.list")
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, condition=lambda x: x.is_text_present("Orders"))

    wait_until_condition(browser, lambda x: x.is_element_present_by_css("#menu-button"))
    browser.find_by_css("#menu-button").first.click()

    wait_until_condition(browser, lambda x: x.is_text_present("Quicklinks"))
    browser.find_by_css(".quicklinks a").first.click()

    wait_until_appeared(browser, ".item-category.item-active")
    browser.find_by_css(".menu-list li a")[2].click()

    wait_until_condition(browser, lambda x: x.is_text_present("New shop product"))


@pytest.mark.browser
@pytest.mark.djangodb
def test_menu_toggle(browser, admin_user, live_server, settings):
    get_default_shop()
    initialize_admin_browser_test(browser, live_server, settings)

    wait_until_condition(browser, lambda x: x.is_text_present("Welcome!"))
    wait_until_condition(browser, lambda x: x.is_text_present("Quicklinks"))

    wait_until_condition(browser, lambda x: x.is_element_present_by_css("#menu-button"))

    # Close menu
    try:
        browser.find_by_css("#menu-button").first.click()
    except selenium.common.exceptions.TimeoutException as e:
        browser.find_by_css("#menu-button").first.click()
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(".desktop-menu-closed"))

    url = reverse("shuup_admin:order.list")
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, condition=lambda x: x.is_text_present("Orders"))

    # Should be closed after page load
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(".desktop-menu-closed"))

    # Open menu
    browser.find_by_css("#menu-button").first.click()
    wait_until_condition(browser, lambda x: not x.is_element_present_by_css(".desktop-menu-closed"))

    url = reverse("shuup_admin:shop_product.list")
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, condition=lambda x: x.is_text_present("Products"))

    # Should be still open after page load
    wait_until_condition(browser, lambda x: not x.is_element_present_by_css(".desktop-menu-closed"))
