# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings


def update_categories_post_save(sender, instance, **kwargs):
    if not getattr(settings, "SHUUP_AUTO_SHOP_PRODUCT_CATEGORIES", False):
        return

    if not instance.pk or not instance.primary_category:
        return

    categories = instance.categories.values_list("pk", flat=True)
    if instance.primary_category.pk not in categories:
        instance.categories.add(instance.primary_category)


def update_categories_through(sender, instance, **kwargs):
    action = kwargs.get("action", "post_add")
    if action != "post_add":
        return

    if not getattr(settings, "SHUUP_AUTO_SHOP_PRODUCT_CATEGORIES", False):
        return

    if not instance.pk:
        return

    if not instance.categories.count():
        return

    if not instance.primary_category:
        instance.primary_category = instance.categories.first()
        instance.save()
