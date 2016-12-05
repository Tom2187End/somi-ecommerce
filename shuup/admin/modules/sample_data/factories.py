# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal
import os
import random
from datetime import datetime, timedelta

import factory.fuzzy as fuzzy
from django.conf import settings
from PIL import Image
from six import BytesIO

from shuup.admin.modules.sample_data import SAMPLE_IMAGES_BASE_DIR
from shuup.core.models import (
    Category, CategoryStatus, PersonContact, Product, ProductMedia,
    ProductMediaKind, SalesUnit, Shop, ShopProduct, ShopProductVisibility
)
from shuup.testing.factories import (
    get_default_product_type, get_default_supplier, get_default_tax_class
)
from shuup.utils.filer import filer_image_from_data


def create_sample_category(name, description, business_segment, image_file, shop):
    category = Category.objects.create(
        name=name,
        description=description,
        status=CategoryStatus.VISIBLE
    )

    image_file_path = os.path.join(SAMPLE_IMAGES_BASE_DIR, image_file)
    path = "ProductCategories/Samples/%s" % business_segment.capitalize()
    filer_image = _filer_image_from_file_path(image_file_path, path)

    category.image = filer_image
    category.shops.add(shop)
    category.save()
    return category


def create_sample_product(name, description, business_segment, image_file, shop):
    product = Product.objects.create(
        name=name,
        description=description,
        type=get_default_product_type(),
        tax_class=get_default_tax_class(),
        sales_unit=SalesUnit.objects.first(),
        sku=fuzzy.FuzzyText(length=10).fuzz()
    )

    image_file_path = os.path.join(SAMPLE_IMAGES_BASE_DIR, image_file)
    path = "ProductImages/Samples/%s" % business_segment.capitalize()
    filer_image = _filer_image_from_file_path(image_file_path, path)

    media = ProductMedia.objects.create(
        product=product,
        kind=ProductMediaKind.IMAGE,
        file=filer_image
    )
    media.shops = Shop.objects.all()
    media.save()
    product.primary_image = media
    product.save()

    sp = ShopProduct.objects.create(
        product=product,
        purchasable=True,
        visibility=ShopProductVisibility.ALWAYS_VISIBLE,
        default_price_value=decimal.Decimal(random.random() * random.randrange(0, 500)),
        shop=shop,
        shop_primary_image=media
    )
    sp.categories = shop.categories.all()
    sp.suppliers.add(get_default_supplier())

    # configure prices
    if "shuup.customer_group_pricing" in settings.INSTALLED_APPS:
        from shuup.customer_group_pricing.models import CgpPrice
        CgpPrice.objects.create(
            product=product,
            price_value=random.randint(15, 340),
            shop=shop,
            group=PersonContact.get_default_group()
        )

    return product


def create_sample_carousel(carousel_data, business_segment, shop):
    if 'shuup.front.apps.carousel' not in settings.INSTALLED_APPS:
        return

    from shuup.front.apps.carousel.models import Carousel, Slide

    carousel = Carousel.objects.create(
        name=carousel_data["name"],
        image_width=carousel_data["width"],
        image_height=carousel_data["height"],
    )

    # available for 365 days
    available_from = datetime.now() - timedelta(days=1)
    available_to = datetime.now() + timedelta(days=365)

    for slide_data in carousel_data["slides"]:
        image_file_path = os.path.join(SAMPLE_IMAGES_BASE_DIR, slide_data["image"])
        path = "CarouselImages/Samples/%s" % business_segment.capitalize()
        filer_image = _filer_image_from_file_path(image_file_path, path)

        slide = Slide.objects.create(
            carousel=carousel,
            caption_text=slide_data["title"],
            available_from=available_from,
            available_to=available_to,
            image=filer_image
        )

        # make sure there is an image for the PARLER_DEFAULT_LANGUAGE_CODE
        default_lang_code = getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE")
        if default_lang_code:
            slide.set_current_language(default_lang_code)
            slide.image = filer_image
            slide.save()

    return carousel


def _filer_image_from_file_path(image_file_path, path):
    _, full_file_name = os.path.split(image_file_path)
    file_name, _ = os.path.splitext(full_file_name)
    image = Image.open(image_file_path)
    sio = BytesIO()
    image.save(sio, format="JPEG")

    return filer_image_from_data(
        request=None,
        path=path,
        file_name="{}.jpeg".format(file_name),
        file_data=sio.getvalue(),
        sha1=True
    )
