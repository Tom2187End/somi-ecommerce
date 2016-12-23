# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from parler.managers import TranslatableQuerySet

from shuup.core import cache

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:  # Py2 fallback
    from urlparse import urlparse, parse_qs


HASHABLE_KEYS = ["customer_groups", "customer", "shop"]

GENERIC_CACHE_NAMESPACE_PREFIX = "generic_context_cache"


def get_cached_value(identifier, item, context, **kwargs):
    """
    Get item from context cache by identifier

    Accepts optional kwargs parameter `allow_cache` which will skip
    fetching the actual cached object. When `allow_cache` is set to
    False only cache key for identifier, item, context combination is
    returned.

    :param identifier: Any
    :type identifier: string
    :param item: Any
    :param context: Any
    :type context: dict
    :return: Cache key and cached value if allowed
    :rtype: tuple(str, object)
    """
    allow_cache = True
    if "allow_cache" in kwargs:
        allow_cache = kwargs.pop("allow_cache")
    key = _get_cache_key_for_context(identifier, item, context, **kwargs)
    if not allow_cache:
        return key, None
    return key, cache.get(key)


def set_cached_value(key, value, timeout=None):
    """
    Set value to context cache

    :param key: Unique key formed to the context
    :param value: Value to cache
    :param timeout: Timeout as seconds
    :type timeout: int
    """
    cache.set(key, value, timeout=timeout)


def bump_cache_for_shop_product(shop_product):
    """
    Bump cache for given shop product

    Clear cache for shop product, product linked to it and
    all the children.

    :param shop_product: shop product object
    :type shop_product: shuup.core.models.ShopProduct
    """
    bump_cache_for_item(shop_product)
    bump_cache_for_item(shop_product.product)

    from shuup.core.models import ShopProduct
    # Bump all children if exists
    for child_shop_products in ShopProduct.objects.filter(product__variation_parent_id=shop_product.product):
        bump_cache_for_item(child_shop_products)
        bump_cache_for_item(child_shop_products.product)

    # Bump parent if exists
    if shop_product.product.variation_parent:
        for sp in ShopProduct.objects.filter(product_id=shop_product.product.variation_parent.id):
            bump_cache_for_item(sp)
            bump_cache_for_item(sp.product)

    # Bump all package parents
    for package_parent in shop_product.product.get_all_package_parents():
        for sp in ShopProduct.objects.filter(product_id=package_parent.id):
            bump_cache_for_item(sp)
            bump_cache_for_item(sp.product)


def bump_cache_for_product(product, shop=None):
    """
    Bump cache for product

    In case shop is not given all the shop products
    for the product is bumped.

    :param product: product object
    :type product: shuup.core.models.Product
    :param shop: shop object
    :type shop: shuup.core.models.Shop|None
    """
    if not shop:
        from shuup.core.models import ShopProduct
        for sp in ShopProduct.objects.filter(product_id=product.id):
            bump_cache_for_shop_product(sp)
    else:
        shop_product = product.get_shop_instance(shop=shop, allow_cache=False)
        bump_cache_for_shop_product(shop_product)


def bump_cache_for_item(item):
    """
    Bump cache for given item

    Use this only for non product items. For products
    and shop_products use `bump_cache_for_product` and
    `bump_cache_for_shop_product` for those.

    :param item: Cached object
    """
    cache.bump_version(_get_namespace_for_item(item))


def bump_cache_for_pk(cls, pk):
    """
    Bump cache for given class and pk combination

    Use this only for non product items. For products
    and shop_products use `bump_cache_for_product` and
    `bump_cache_for_shop_product` for those.

    In case you need to use this to product or shop_product
    make sure you also bump related objects like in
    `bump_cache_for_shop_product`.

    :param cls: Class for cached object
    :param pk: pk for cached object
    """
    cache.bump_version("%s-%s" % (_get_namespace_prefix(cls), pk))


def bump_product_signal_handler(sender, instance, **kwargs):
    """
    Signal handler for clearing product cache

    :param instance: Shuup product
    :type instance: shuup.core.models.Product
    """
    bump_cache_for_product(instance)


def bump_shop_product_signal_handler(sender, instance, **kwargs):
    """
    Signal handler for clearing shop product cache

    :param instance: Shuup shop product
    :type instance: shuup.core.models.ShopProduct
    """
    bump_cache_for_shop_product(instance)


def _get_cache_key_for_context(identifier, item, context, **kwargs):
    namespace = _get_namespace_for_item(item)

    items = _get_items_from_context(context)

    for k, v in six.iteritems(kwargs):
        items[k] = _get_val(v)

    if isinstance(context, WSGIRequest):
        query_string = urlparse(context.get_full_path()).query
        for k, v in six.iteritems(parse_qs(query_string)):
            items[k] = _get_val(v)

    return "%s:%s_%s" % (namespace, identifier, hash(frozenset(items.items())))


def _get_items_from_context(context):
    items = {}
    if hasattr(context, "items"):
        for k, v in six.iteritems(context):
            if k in HASHABLE_KEYS:
                if k == "customer" and hasattr(v, "groups"):
                    v = v.groups.all()
                    k = "customer_groups"
                items[k] = _get_val(v)
    else:
        for key in HASHABLE_KEYS:
            val = None
            if hasattr(context, key):
                if key == "customer":
                    # some context only has customer, transfer this to customer groups
                    val = "|".join(list(map(str, getattr(context, key).groups.all().values_list("pk", flat=True))))
                    key = "customer_groups"
                else:
                    val = _get_val(getattr(context, key))
            items[key] = val
    return items


def _get_val(v):
    if isinstance(v, dict):
        return hash(frozenset(v.items()))
    if hasattr(v, "pk"):
        return v.pk
    if isinstance(v, QuerySet) or isinstance(v, TranslatableQuerySet):
        return "|".join(list(map(str, v.all().values_list("pk", flat=True))))
    if isinstance(v, list):
        return "|".join(list(map(str, v)))
    return v


def _get_namespace_for_item(item):
    return "%s-%s" % (_get_namespace_prefix(item), _get_item_id(item))


def _get_namespace_prefix(item):
    if hasattr(item, "_meta"):
        model_meta = item._meta
        return "%s-%s" % (model_meta.app_label, model_meta.model_name)
    return GENERIC_CACHE_NAMESPACE_PREFIX


def _get_item_id(item):
    if isinstance(item, int):
        return item

    item_id = 0
    if item:
        if hasattr(item, "pk"):
            item_id = item.pk or 0
        else:
            item_id = item.__class__.lower() if callable(item) else 0
    return item_id
