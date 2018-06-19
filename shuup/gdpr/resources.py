# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.template import loader
from django.templatetags.static import static

from shuup.core.shop_provider import get_shop
from shuup.gdpr.models import GDPRCookieCategory, GDPRSettings
from shuup.utils.djangoenv import has_installed
from shuup.xtheme.resources import add_resource, InlineMarkupResource


def valid_view(context):
    view_class = getattr(context["view"], "__class__", None) if context.get("view") else None
    if not view_class or not context.get("request"):
        return False

    request = context.get("request")
    if request:
        match = request.resolver_match
        if match and match.app_name == "shuup_admin":
            return False

    view_name = getattr(view_class, "__name__", "")
    if view_name == "EditorView":
        return False
    return True


def add_gdpr_consent_resources(context, content):
    if not valid_view(context):
        return

    shop = get_shop(context["request"])
    gdpr_settings = GDPRSettings.get_for_shop(shop)

    # GDPR not enabled
    if not gdpr_settings.enabled:
        return

    # consent already added
    # TODO: Should we check for changes and ask the consent again here?
    if settings.SHUUP_GDPR_CONSENT_COOKIE_NAME in context["request"].COOKIES:
        return

    gdpr_documents = []
    if has_installed("shuup.simple_cms"):
        from shuup.simple_cms.models import Page, PageType
        gdpr_documents = Page.objects.visible(shop).filter(page_type=PageType.REVISIONED)

    render_context = {
        "request": context["request"],
        "csrf_token": context["csrf_token"],
        "gdpr_settings": gdpr_settings,
        "gdpr_documents": gdpr_documents,
        "gdpr_cookie_categories": GDPRCookieCategory.objects.filter(shop=shop)
    }
    html_resource = InlineMarkupResource(
        loader.render_to_string("shuup/gdpr/gdpr_consent.jinja", context=render_context)
    )
    add_resource(context, "body_end", html_resource)
    add_resource(context, "body_end", static("shuup_gdpr/shuup_gdpr.js"))
    add_resource(context, "head_end", static("shuup_gdpr/shuup_gdpr_styles.css"))
