# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, Picotable, RangeFilter, TextFilter
)
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import ProductMode, Shop, ShopProduct


class ProductPicotable(Picotable):
    def process_item(self, object):
        out = super(ProductPicotable, self).process_item(object)
        popup = self.request.GET.get("popup")
        kind = self.request.GET.get("kind", "")
        if popup and kind == "product":  # Enable option to pick products
            out.update({"_id": object.product.id})
        return out


class ProductListView(PicotableListView):
    model = ShopProduct
    picotable_class = ProductPicotable

    default_columns = [
        Column(
            "primary_image",
            _(u"Primary Image"),
            display="get_primary_image",
            class_name="text-center",
            raw=True,
            ordering=1,
            sortable=False),
        Column(
            "name",
            _(u"Name"),
            sort_field="product__translations__name",
            display="product__name",
            filter_config=TextFilter(
                filter_field="product__translations__name",
                placeholder=_("Filter by name...")
            ),
            ordering=2),
        Column(
            "sku",
            _(u"SKU"),
            display="product__sku",
            filter_config=RangeFilter(filter_field="product__sku"),
            ordering=3),
        Column(
            "barcode",
            _(u"Barcode"),
            display="product__barcode",
            filter_config=TextFilter(placeholder=_("Filter by barcode...")),
            ordering=4),
        Column(
            "mode",
            _(u"Mode"),
            display="product__mode",
            filter_config=ChoicesFilter(ProductMode.choices),
            ordering=5),
        Column(
            "primary_category",
            _("Primary Category"),
            display=(lambda instance: instance.primary_category.name if instance.primary_category else None),
            filter_config=TextFilter(
                filter_field="primary_category__translations__name",
                placeholder=_("Filter by category name...")
            ),
            ordering=6),
        Column(
            "categories",
            _("Categories"),
            display="format_categories",
            filter_config=TextFilter(
                filter_field="categories__translations__name",
                placeholder=_("Filter by category name...")
            ),
            ordering=7)
    ]

    related_objects = [
        ("product", "shuup.core.models:Product"),
    ]

    mass_actions = [
        "shuup.admin.modules.products.mass_actions:VisibleMassAction",
        "shuup.admin.modules.products.mass_actions:InvisibleMassAction",
        "shuup.admin.modules.products.mass_actions:FileResponseAction",
        "shuup.admin.modules.products.mass_actions:EditProductAttributesAction",
    ]
    toolbar_buttons_provider_key = "product_list_toolbar_provider"

    def format_categories(self, instance):
        return ", ".join(list(instance.categories.values_list("translations__name", flat=True)))

    def get_columns(self):
        for column in self.columns:
            if column.id == 'shop':
                shops = Shop.objects.get_for_user(self.request.user).prefetch_related('translations')
                column.filter_config = ChoicesFilter(choices=shops)
                break
        return self.columns

    def get_primary_image(self, instance):
        if instance.product.primary_image:
            thumbnail = instance.product.primary_image.get_thumbnail()
            if thumbnail:
                return "<img src='/media/{}'>".format(thumbnail)
        return "<img src='%s'>" % static("shuup_admin/img/no_image_thumbnail.png")

    def get_queryset(self):
        filter = self.get_filter()
        shop = self.request.shop
        qs = ShopProduct.objects.filter(product__deleted=False, shop=shop)
        q = Q()
        for mode in filter.get("modes", []):
            q |= Q(product__mode=mode)
        manufacturer_ids = filter.get("manufacturers")
        if manufacturer_ids:
            q |= Q(product__manufacturer_id__in=manufacturer_ids)
        qs = qs.filter(q)
        return qs

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance.product, "class": "header"},
            {"title": _(u"Barcode"), "text": item.get("product__barcode")},
            {"title": _(u"SKU"), "text": item.get("product__sku")},
            {"title": _(u"Type"), "text": item.get("product__type")},
        ]
