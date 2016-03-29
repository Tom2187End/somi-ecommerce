# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.simple_cms.plugins import PageLinksPlugin
from shoop_tests.front.fixtures import get_jinja_context

from .utils import create_page


@pytest.mark.django_db
def test_page_links_plugin_visible_in_menu():
    """
    Make sure plugin correctly filters out pages that are not set to be
    visible in menus
    """
    context = get_jinja_context()
    page = create_page(eternal=True, visible_in_menu=True)
    plugin = PageLinksPlugin({"pages": [page.pk]})
    assert page in plugin.get_context_data(context)["pages"]

    page.visible_in_menu = False
    page.save()
    assert page not in plugin.get_context_data(context)["pages"]


@pytest.mark.django_db
def test_page_links_plugin_hide_expired():
    """
    Make sure plugin correctly filters out expired pages based on plugin
    configuration
    """
    context = get_jinja_context()
    page = create_page(eternal=True, visible_in_menu=True)
    plugin = PageLinksPlugin({"pages": [page.pk]})
    assert page in plugin.get_context_data(context)["pages"]

    page.available_from = None
    page.available_to = None
    page.save()
    assert page in plugin.get_context_data(context)["pages"]

    plugin.config["hide_expired"] = True
    assert page not in plugin.get_context_data(context)["pages"]


@pytest.mark.django_db
def test_page_links_plugin_show_all():
    """
    Test that show_all_pages forces plugin to return all visible pages
    """
    context = get_jinja_context()
    page = create_page(eternal=True, visible_in_menu=True)
    plugin = PageLinksPlugin({"show_all_pages": False})
    assert not plugin.get_context_data(context)["pages"]

    plugin = PageLinksPlugin({"show_all_pages": True})
    assert page in plugin.get_context_data(context)["pages"]
