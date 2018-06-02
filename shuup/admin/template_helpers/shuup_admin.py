# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

"""
This module is installed as the `shuup_admin` template function namespace.
"""

import itertools

from django.conf import settings
from django.core.urlresolvers import NoReverseMatch, reverse
from django.middleware.csrf import get_token
from jinja2.utils import contextfunction

from shuup import configuration
from shuup.admin import menu
from shuup.admin.breadcrumbs import Breadcrumbs
from shuup.admin.utils.urls import (
    get_model_url, manipulate_query_string, NoModelUrl
)
from shuup.core.models import Shop
from shuup.core.telemetry import is_telemetry_enabled

__all__ = ["get_menu_entry_categories", "get_front_url", "get_config", "model_url"]


@contextfunction
def get_quicklinks(context):
    request = context["request"]
    if request.GET.get("context") == "home":
        return []
    return menu.get_quicklinks(request=context["request"])


@contextfunction
def get_menu_entry_categories(context):
    return menu.get_menu_entry_categories(request=context["request"])


@contextfunction
def get_menu_entries(context):
    return sorted(itertools.chain(*(
        c.entries
        for c
        in menu.get_menu_entry_categories(request=context["request"]).values()
    )), key=(lambda m: m.text))


@contextfunction
def get_front_url(context):
    front_url = context.get("front_url")
    if not front_url:
        try:
            front_url = reverse("shuup:index")
        except NoReverseMatch:
            front_url = None
    return front_url


@contextfunction
def get_support_id(context):
    support_id = None
    if is_telemetry_enabled():
        support_id = configuration.get(None, "shuup_support_id")
    return support_id


# TODO: Figure out a more extensible way to deal with this
BROWSER_URL_NAMES = {
    "select": "shuup_admin:select",
    "media": "shuup_admin:media.browse",
    "product": "shuup_admin:shop_product.list",
    "contact": "shuup_admin:contact.list",
    "setLanguage": "shuup_admin:set-language",
    "tour": "shuup_admin:tour"
}


def get_browser_urls():
    browser_urls = {}
    for name, urlname in BROWSER_URL_NAMES.items():
        try:
            browser_urls[name] = reverse(urlname)
        except NoReverseMatch:  # This may occur when a module is not available.
            browser_urls[name] = None
    return browser_urls


@contextfunction
def get_config(context):
    request = context["request"]
    url_name = None
    if getattr(request, "resolver_match", None):
        # This does not exist when testing views directly
        url_name = request.resolver_match.url_name

    qs = {"context": url_name}
    return {
        "searchUrl": manipulate_query_string(reverse("shuup_admin:search"), **qs),
        "menuUrl": manipulate_query_string(reverse("shuup_admin:menu"), **qs),
        "browserUrls": get_browser_urls(),
        "csrf": get_token(request)
    }


@contextfunction
def get_breadcrumbs(context):
    breadcrumbs = context.get("breadcrumbs")
    if breadcrumbs is None:
        breadcrumbs = Breadcrumbs.infer(context)
    return breadcrumbs


@contextfunction
def model_url(context, model, kind="detail", default=None):
    """
    Get a model URL of the given kind for a model (instance or class).

    :param context: Jinja rendering context
    :type context: jinja2.runtime.Context
    :param model: The model instance or class.
    :type model: django.db.Model
    :param kind: The URL kind to retrieve. See `get_model_url`.
    :type kind: str
    :param default: Default value to return if model URL retrieval fails.
    :type default: str
    :return: URL string.
    :rtype: str
    """
    user = context.get("user")
    try:
        request = context.get("request")
        shop = request.shop if request else None
        return get_model_url(model, kind=kind, user=user, shop=shop)
    except NoModelUrl:
        return default


@contextfunction
def get_shop_count(context):
    """
    Return the number of shops accessible by the currently logged in user
    """
    request = context["request"]
    if not request or request.user.is_anonymous():
        return 0
    return Shop.objects.get_for_user(request.user).count()


@contextfunction
def get_admin_shop(context):
    return context["request"].shop


@contextfunction
def is_multishop_enabled(context):
    return settings.SHUUP_ENABLE_MULTIPLE_SHOPS is True
