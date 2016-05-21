# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import get_language
from jinja2.utils import contextfunction
from mptt.templatetags.mptt_tags import cache_tree_children

from shoop.core.models import Category, Manufacturer, Product, Supplier
from shoop.front.utils.product_statistics import get_best_selling_product_info
from shoop.front.utils.views import cache_product_things
from shoop.utils.translation import cache_translations_for_tree


@contextfunction
def get_visible_products(context, n_products, ordering=None, filter_dict=None, orderable_only=True):
    """
    :param context: Rendering context
    :type context: jinja2.runtime.Context
    :param n_products: Number of products to return
    :type n_products: int
    :param ordering: String specifying ordering
    :type ordering: str
    :param filter_dict: Dictionary of filter parameters
    :type filter_dict: dict[str, object]
    :param orderable_only: Boolean limiting results to orderable products
    :type orderable_only: bool
    :rtype: shoop.core.models._products.ProductQuerySet
    """
    request = context["request"]
    customer = request.customer
    shop = request.shop
    products_qs = Product.objects.list_visible(
        shop=shop,
        customer=customer,
        language=get_language(),
    )

    if ordering:
        products_qs = products_qs.order_by(ordering)
    if not filter_dict:
        filter_dict = {}
    supplier_filter = Q()
    if orderable_only:
        for supplier in Supplier.objects.all():
            supplier_filter |= Q(shop_products__pk__in=supplier.get_suppliable_products(shop, customer))
        products_qs = products_qs.filter(supplier_filter)

    return products_qs.filter(**filter_dict)[:n_products]


@contextfunction
def get_best_selling_products(context, n_products=12, cutoff_days=30, orderable_only=True):
    request = context["request"]
    data = get_best_selling_product_info(
        shop_ids=[request.shop.pk],
        cutoff_days=cutoff_days
    )
    product_ids = [d[0] for d in data][:n_products]
    products = get_visible_products(
        context,
        n_products,
        filter_dict={"id__in": product_ids},
        orderable_only=orderable_only,
    )
    products = cache_product_things(request, products)
    products = sorted(products, key=lambda p: product_ids.index(p.id))  # pragma: no branch
    products = products[:n_products]
    return products


@contextfunction
def get_newest_products(context, n_products=6, orderable_only=True):
    request = context["request"]
    products = get_visible_products(
        context,
        n_products,
        ordering="-pk",
        orderable_only=orderable_only,
    )
    products = cache_product_things(request, products)
    return products


@contextfunction
def get_random_products(context, n_products=6, orderable_only=True):
    request = context["request"]
    products = get_visible_products(
        context,
        n_products,
        ordering="?",
        orderable_only=orderable_only,
    )
    products = cache_product_things(request, products)
    return products


@contextfunction
def get_all_manufacturers(context):
    request = context["request"]
    products = Product.objects.list_visible(shop=request.shop, customer=request.customer)
    manufacturers_ids = products.values_list("manufacturer__id").distinct()
    manufacturers = Manufacturer.objects.filter(pk__in=manufacturers_ids)
    return manufacturers


@contextfunction
def get_root_categories(context):
    request = context["request"]
    language = get_language()
    roots = cache_tree_children(
        Category.objects.all_visible(
            customer=request.customer, shop=request.shop, language=language))
    cache_translations_for_tree(roots, languages=[language])
    return roots


@contextfunction
def get_pagination_variables(context, objects, limit):
    """
    Get pagination variables for template

    :param context: template context
    :param objects: objects paginated
    :param limit: per page limit
    :return: variables to render object-list with pagination
    """
    variables = {"objects": objects}

    variables["paginator"] = paginator = Paginator(objects, limit)
    variables["is_paginated"] = (paginator.num_pages > 1)
    try:
        current_page = int(context["request"].GET.get("page") or 0)
    except ValueError:
        current_page = 1
    page = paginator.page(min((current_page or 1), paginator.num_pages))
    variables["page"] = page
    variables["objects"] = page.object_list

    return variables
