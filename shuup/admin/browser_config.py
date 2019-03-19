# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings


class BaseBrowserConfigProvider(object):
    @classmethod
    def get_browser_urls(cls, request, **kwargs):
        return {}

    @classmethod
    def get_gettings(cls, request, **kwargs):
        return {}


class DefaultBrowserConfigProvider(BaseBrowserConfigProvider):
    @classmethod
    def get_browser_urls(cls, request, **kwargs):
        return {
            "edit": "shuup_admin:edit",
            "select": "shuup_admin:select",
            "media": "shuup_admin:media.browse",
            "product": "shuup_admin:shop_product.list",
            "contact": "shuup_admin:contact.list",
            "setLanguage": "shuup_admin:set-language",
            "tour": "shuup_admin:tour",
            "menu_toggle": "shuup_admin:menu_toggle"
        }

    @classmethod
    def get_gettings(cls, request, **kwargs):
        return {
            "minSearchInputLength": settings.SHUUP_ADMIN_MINIMUM_INPUT_LENGTH_SEARCH or 1
        }
