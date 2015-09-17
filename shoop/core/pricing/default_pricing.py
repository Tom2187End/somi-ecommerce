# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shoop.core.models import ShopProduct
from shoop.core.pricing import PriceInfo, PricingContext, PricingModule, TaxfulPrice, TaxlessPrice


class DefaultPricingContext(PricingContext):
    REQUIRED_VALUES = ["shop"]
    shop = None


class DefaultPricingModule(PricingModule):
    identifier = "default_pricing"
    name = _("Default Pricing")

    pricing_context_class = DefaultPricingContext

    def get_context_from_request(self, request):
        """
        Inject shop into pricing context.

        Shop information is used to find correct `ShopProduct`
        in `self.get_price_info`
        """
        return self.pricing_context_class(shop=request.shop)

    def get_price_info(self, context, product, quantity=1):
        """
        Return a `PriceInfo` calculated from `ShopProduct.default_price`

        Since `ShopProduct.default_price` can be `None` it will
        be set to zero (0) if `None`.
        """
        shop_product = ShopProduct.objects.get(product=product, shop=context.shop)

        default_price = (shop_product.default_price or 0)

        price_cls = (TaxfulPrice if context.shop.prices_include_tax else TaxlessPrice)
        return PriceInfo(
            price=price_cls(default_price * quantity),
            base_price=price_cls(default_price * quantity),
            quantity=quantity,
        )
