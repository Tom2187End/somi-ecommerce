# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.transaction import atomic

from shuup.utils.models import copy_model_instance
from shuup.core.models import (
    Product, ProductAttribute, ProductMedia, ShopProduct
)
from shuup.admin.signals import product_copied
from shuup.utils.models import get_data_dict


class ProductCloner():
    def __init__(self, current_shop, current_supplier):
        self.current_shop = current_shop
        self.current_supplier = current_supplier

    @atomic()
    def clone_product(self, shop_product=None):
        # Clone product
        product = shop_product.product
        new_product = copy_model_instance(product)
        new_product.sku = "{}-{}".format(product.sku, Product.objects.count())
        new_product.name = ("{name} - Copy").format(name=product.name)
        new_product.save()

        # Change the name so it will automatically create a translation record
        for trans in product.translations.all()[1:]:
            trans_product_data = get_data_dict(trans)
            trans_product_data['master'] = new_product
            Product._parler_meta.get_model_by_related_name('translations').objects.create(**trans_product_data)

        # Clone shop_product
        new_shop_product = copy_model_instance(shop_product)
        new_shop_product.product = new_product
        new_shop_product.save()
        for trans in shop_product.translations.all():
            trans_shop_product_data = get_data_dict(trans)
            trans_shop_product_data['master'] = new_shop_product
            ShopProduct._parler_meta.get_model_by_related_name('translations').objects.create(**trans_shop_product_data)

        if self.current_supplier:
            new_shop_product.suppliers.add(self.current_supplier)
        else:
            new_shop_product.suppliers.set(shop_product.suppliers.all())

        new_shop_product.categories.set(shop_product.categories.all())
        for attribute in product.attributes.all():
            ProductAttribute.objects.create(product=new_product, attribute=attribute.attribute, value=attribute.value)

        # Clone media
        for media in product.media.all():
            media_copy = copy_model_instance(media)
            media_copy.product = new_product
            media_copy.file = media.file
            media.shops.add(shop_product.shop)
            if product.primary_image == media:
                new_product.primary_image = media_copy

            for trans in media.translations.all():
                trans_product_media_data = get_data_dict(trans)
                trans_product_media_data['master'] = new_shop_product
                ProductMedia._parler_meta.get_model_by_related_name('translations').objects.create(
                    **trans_product_media_data)
            media_copy.save()

        product_copied.send(
            sender=type(self), shop=shop_product.shop, suppliers=self.current_supplier,
            copied=product, copy=new_product)

        return new_shop_product
