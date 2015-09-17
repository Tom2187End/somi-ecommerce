# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shoop.core.models import ShopProduct
from shoop.core.pricing import PriceInfo, PricingContext, PricingModule, TaxfulPrice, TaxlessPrice

from .models import SimpleProductPrice


class SimplePricingContext(PricingContext):
    REQUIRED_VALUES = ("customer_group_ids", "shop")
    customer_group_ids = ()
    shop = None


class SimplePricingModule(PricingModule):
    identifier = "simple_pricing"
    name = _("Simple Pricing")

    pricing_context_class = SimplePricingContext

    def get_context_from_request(self, request):
        customer = getattr(request, "customer", None)

        if not customer or customer.is_anonymous:
            customer_group_ids = []
        else:
            customer_group_ids = sorted(customer.groups.all().values_list("id", flat=True))

        return self.pricing_context_class(
            shop=request.shop,
            customer_group_ids=customer_group_ids
        )

    def get_price_info(self, context, product, quantity=1):

        if isinstance(product, six.integer_types):
            product_id = product
            shop_product = ShopProduct.objects.get(product_id=product_id, shop_id=context.shop.pk)
        else:
            shop_product = product.get_shop_instance(context.shop)
            product_id = product.pk

        default_price = (shop_product.default_price or 0)

        includes_tax = context.shop.prices_include_tax

        if context.customer_group_ids:
            filter = Q(price__gt=0, product=product_id, shop=context.shop, group__in=context.customer_group_ids)
            result = (
                SimpleProductPrice.objects.filter(filter)
                .order_by("price")[:1]
                .values_list("price", flat=True)
            )
        else:
            result = None

        if result:
            price = result[0]
            if default_price > 0:
                price = min([default_price, price])
        else:
            price = default_price

        price_cls = (TaxfulPrice if includes_tax else TaxlessPrice)
        return PriceInfo(
            price=price_cls(price * quantity),
            base_price=price_cls(price * quantity),
        )
