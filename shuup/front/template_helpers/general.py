# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import math
from collections import defaultdict

import six
from django.conf import settings
from django.core.paginator import Paginator
from django.utils.translation import get_language, get_language_info, ugettext
from jinja2.utils import contextfunction
from mptt.templatetags.mptt_tags import cache_tree_children

from shuup.core.models import (
    Category, Manufacturer, Product, ShopProduct, Supplier
)
from shuup.core.utils import context_cache
from shuup.front.utils.product_statistics import get_best_selling_product_info
from shuup.front.utils.views import cache_product_things
from shuup.utils.translation import cache_translations_for_tree


@contextfunction
def get_listed_products(context, n_products, ordering=None, filter_dict=None, orderable_only=True):
    """
    Returns all products marked as listed that are determined to be
    visible based on the current context.

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
    :rtype: list[shuup.core.models.Product]
    """
    request = context["request"]
    customer = request.customer
    shop = request.shop

    # Todo: Check if this should be cached

    if not filter_dict:
        filter_dict = {}
    products_qs = Product.objects.listed(
        shop=shop,
        customer=customer,
        language=get_language(),
    ).filter(**filter_dict)

    if ordering:
        products_qs = products_qs.order_by(ordering)

    if orderable_only:
        suppliers = Supplier.objects.all()
        products = []
        for product in products_qs[:(n_products * 4)]:
            if len(products) == n_products:
                break
            shop_product = product.get_shop_instance(shop, allow_cache=True)
            for supplier in suppliers:
                if shop_product.is_orderable(supplier, customer, shop_product.minimum_purchase_quantity):
                    products.append(product)
                    break
        return products

    products = products_qs[:n_products]
    return products


def _can_use_cache(products, shop, customer):
    """
    Check whether the cached products can be still used

    If any of the products is no more orderable refetch the products
    """
    product_ids = [prod.id for prod in products]
    for supplier in Supplier.objects.all():
        for sp in ShopProduct.objects.filter(product__id__in=product_ids):
            if not sp.is_orderable(supplier, customer=customer, quantity=sp.minimum_purchase_quantity):
                return False
    return True


@contextfunction
def get_best_selling_products(context, n_products=12, cutoff_days=30, orderable_only=True):
    request = context["request"]

    key, products = context_cache.get_cached_value(
        identifier="best_selling_products", item=None, context=request,
        n_products=n_products, cutoff_days=cutoff_days, orderable_only=orderable_only)
    if products is not None and _can_use_cache(products, request.shop, request.customer):
        return products

    products = _get_best_selling_products(cutoff_days, n_products, orderable_only, request)
    context_cache.set_cached_value(key, products, settings.SHUUP_TEMPLATE_HELPERS_CACHE_DURATION)
    return products


def _get_best_selling_products(cutoff_days, n_products, orderable_only, request):
    data = get_best_selling_product_info(
        shop_ids=[request.shop.pk],
        cutoff_days=cutoff_days
    )
    combined_variation_products = defaultdict(int)
    for product_id, parent_id, qty in data:
        if parent_id:
            combined_variation_products[parent_id] += qty
        else:
            combined_variation_products[product_id] += qty
    product_ids = [
        d[0] for
        d in sorted(six.iteritems(combined_variation_products), key=lambda i: i[1], reverse=True)
    ][:n_products]
    products = []
    if orderable_only:
        # get suppliers for later use
        suppliers = Supplier.objects.all()
    for product in Product.objects.filter(id__in=product_ids):
        shop_product = product.get_shop_instance(request.shop, allow_cache=True)
        if orderable_only:
            for supplier in suppliers:
                if shop_product.is_orderable(supplier, request.customer, shop_product.minimum_purchase_quantity):
                    products.append(product)
                    break
        elif shop_product.is_visible(request.customer):
            products.append(product)
    products = cache_product_things(request, products)
    products = sorted(products, key=lambda p: product_ids.index(p.id))  # pragma: no branch
    return products


@contextfunction
def get_newest_products(context, n_products=6, orderable_only=True):
    request = context["request"]
    key, products = context_cache.get_cached_value(
        identifier="newest_products", item=None, context=request,
        n_products=n_products, orderable_only=orderable_only)
    if products is not None and _can_use_cache(products, request.shop, request.customer):
        return products

    products = get_listed_products(
        context,
        n_products,
        ordering="-pk",
        filter_dict={
            "variation_parent": None
        },
        orderable_only=orderable_only,
    )
    products = cache_product_things(request, products)
    context_cache.set_cached_value(key, products, settings.SHUUP_TEMPLATE_HELPERS_CACHE_DURATION)
    return products


@contextfunction
def get_random_products(context, n_products=6, orderable_only=True):
    request = context["request"]
    key, products = context_cache.get_cached_value(
        identifier="random_products", item=None, context=request,
        n_products=n_products, orderable_only=orderable_only)
    if products is not None and _can_use_cache(products, request.shop, request.customer):
        return products

    products = get_listed_products(
        context,
        n_products,
        ordering="?",
        filter_dict={
            "variation_parent": None
        },
        orderable_only=orderable_only,
    )
    products = cache_product_things(request, products)
    context_cache.set_cached_value(key, products, settings.SHUUP_TEMPLATE_HELPERS_CACHE_DURATION)
    return products


@contextfunction
def get_products_for_category(context, category, n_products=6, orderable_only=True):
    request = context["request"]
    key, products = context_cache.get_cached_value(
        identifier="products_for_category", item=None, context=request,
        n_products=n_products, category=category, orderable_only=orderable_only)
    if products is not None and _can_use_cache(products, request.shop, request.customer):
        return products

    products = get_listed_products(
        context,
        n_products,
        ordering="?",
        filter_dict={
            "variation_parent": None,
            "shop_products__categories__in": category
        },
        orderable_only=orderable_only,
    )
    products = cache_product_things(request, products)
    context_cache.set_cached_value(key, products, settings.SHUUP_TEMPLATE_HELPERS_CACHE_DURATION)
    return products


@contextfunction
def get_all_manufacturers(context):
    request = context["request"]
    key, manufacturers = context_cache.get_cached_value(
        identifier="all_manufacturers", item=None, context=request)
    if manufacturers is not None:
        return manufacturers

    products = Product.objects.listed(shop=request.shop, customer=request.customer)
    manufacturers_ids = products.values_list("manufacturer__id").distinct()
    manufacturers = Manufacturer.objects.filter(pk__in=manufacturers_ids)
    context_cache.set_cached_value(key, manufacturers, settings.SHUUP_TEMPLATE_HELPERS_CACHE_DURATION)
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
        requested_page = int(context["request"].GET.get("page") or 0)
    except ValueError:
        requested_page = 0
    current_page = min(max(requested_page, 1), paginator.num_pages)
    page = paginator.page(current_page)
    variables["page"] = page
    variables["page_range"] = _get_page_range(current_page, paginator.num_pages)
    variables["objects"] = page.object_list

    return variables


def _get_page_range(current_page, num_pages, range_gap=5):
    current_page = min(current_page, num_pages + 1)
    if current_page <= math.ceil(range_gap / 2):
        start = 1
        end = range_gap + 1
    elif num_pages - math.ceil(range_gap / 2) < current_page:
        start = num_pages - range_gap + 1
        end = num_pages + 1
    else:
        start = current_page - range_gap // 2
        end = current_page + range_gap // 2 + 1
    return six.moves.range(start, min(end, num_pages + 1))


@contextfunction
def get_shop_language_choices(context):
    languages = []
    for code, name in settings.LANGUAGES:
        lang_info = get_language_info(code)
        name_in_current_lang = ugettext(name)
        local_name = lang_info["name_local"]
        languages.append((code, name_in_current_lang, local_name))
    return languages
