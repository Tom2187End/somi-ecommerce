# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from filer.models import File

from shuup.admin.base import AdminModule, MenuEntry, SearchResult
from shuup.admin.menu import PRODUCTS_MENU_CATEGORY
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.admin.utils.urls import (
    admin_url, derive_model_url, get_edit_and_list_urls, get_model_url
)
from shuup.core.models import Category


class CategoryModule(AdminModule):
    name = _("Categories")
    category = _("Products")
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shuup_admin:category.list", category=PRODUCTS_MENU_CATEGORY)

    def get_urls(self):
        return [
            admin_url(
                "^categories/(?P<pk>\d+)/copy-visibility/$",
                "shuup.admin.modules.categories.views.CategoryCopyVisibilityView",
                name="category.copy_visibility",
                permissions=get_default_model_permissions(Category)
            ),
            admin_url(
                "^categories/(?P<pk>\d+)/delete/$",
                "shuup.admin.modules.categories.views.CategoryDeleteView",
                name="category.delete",
                permissions=get_default_model_permissions(Category)
            ),
        ] + get_edit_and_list_urls(
            url_prefix="^categories",
            view_template="shuup.admin.modules.categories.views.Category%sView",
            name_template="category.%s",
            permissions=get_default_model_permissions(Category),
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Categories"), icon="fa fa-sitemap",
                url="shuup_admin:category.list", category=PRODUCTS_MENU_CATEGORY, ordering=2
            )
        ]

    def get_search_results(self, request, query):
        minimum_query_length = 3
        if len(query) >= minimum_query_length:
            categories = Category.objects.filter(
                Q(translations__name__icontains=query) |
                Q(identifier__icontains=query)
            ).distinct().order_by("tree_id", "lft")
            for i, category in enumerate(categories[:10]):
                relevance = 100 - i
                yield SearchResult(
                    text=six.text_type(category),
                    url=get_model_url(category),
                    category=self.category,
                    relevance=relevance
                )

    def get_required_permissions(self):
        return get_default_model_permissions(Category) | get_default_model_permissions(File)

    def get_model_url(self, object, kind):
        return derive_model_url(Category, "shuup_admin:category", object, kind)
