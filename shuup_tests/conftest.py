# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from django.core.signals import setting_changed

from shuup.apps.provides import clear_provides_cache
from shuup.testing.factories import get_default_shop
from shuup.utils.importing import clear_load_cache
from shuup.xtheme.testing import override_current_theme_class
from shuup.utils.i18n import get_language_name


def clear_caches(setting, **kwargs):
    clear_load_cache()
    if setting == "INSTALLED_APPS":
        clear_provides_cache()


def pytest_configure(config):
    setting_changed.connect(clear_caches, dispatch_uid="shuup_test_clear_caches")
    settings.SHUUP_TELEMETRY_ENABLED = False


def pytest_runtest_call(item):
    # All tests are run with a theme override `shuup.themes.classic_gray.ClassicGrayTheme`.
    # To un-override, use `with override_current_theme_class()` (no arguments to re-enable database lookup)
    from shuup.themes.classic_gray.theme import ClassicGrayTheme
    item.session._theme_overrider = override_current_theme_class(ClassicGrayTheme, get_default_shop())
    item.session._theme_overrider.__enter__()
    get_language_name.cache_clear()  # Clear language name lru_cache for each test


def pytest_runtest_teardown(item, nextitem):
    if hasattr(item.session, "_theme_overrider"):
        item.session._theme_overrider.__exit__(None, None, None)
        del item.session._theme_overrider


@pytest.fixture(scope="session")
def splinter_make_screenshot_on_failure():
    return False


# use django_db on every test
# activate the EN language by default
# initialize a new cache
@pytest.fixture(autouse=True)
def enable_db_access(db):
    from django.utils.translation import activate
    activate("en")

    # make sure the default cache is also cleared
    # it is used by third party apps like parler
    from django.core.cache import cache
    cache.clear()

    from shuup.core import cache
    cache.init_cache()


# always make ShopProduct id different from Product id
@pytest.fixture(autouse=True)
def break_shop_product_id_sequence(db):
    from shuup.core.models import ShopProduct
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("INSERT INTO SQLITE_SEQUENCE (name, seq) values ('%s', 1500)" % ShopProduct._meta.db_table)


@pytest.fixture()
def staff_user():
    from django.contrib.auth import get_user_model
    return get_user_model().objects.create(is_staff=True, is_superuser=False, username="staff_user")
