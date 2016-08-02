# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import random

from django.db import models
from django.utils.translation import ugettext_lazy as _

from shuup.core.fields import MoneyValueField
from shuup.core.models import (
    Category, OrderLineType, PolymorphicShuupModel, Product
)
from shuup.core.order_creator._source import LineSource


class BasketLineEffect(PolymorphicShuupModel):
    identifier = None
    model = None
    admin_form_class = None

    campaign = models.ForeignKey("BasketCampaign", related_name='line_effects', verbose_name=_("campaign"))

    def get_discount_lines(self, order_source, original_lines):
        """
        Applies the effect based on given `order_source`

        :return: amount of discount to accumulate for the product
        :rtype: Iterable[shuup.core.order_creator.SourceLine]
        """
        raise NotImplementedError("Not implemented!")


class FreeProductLine(BasketLineEffect):
    identifier = "free_product_line_effect"
    model = Product
    name = _("Free Product(s)")

    quantity = models.PositiveIntegerField(default=1, verbose_name=_("quantity"))
    products = models.ManyToManyField(Product, verbose_name=_("product"))

    @property
    def description(self):
        return _("Select product(s) to give free.")

    @property
    def values(self):
        return self.products

    @values.setter
    def values(self, values):
        self.products = values

    def get_discount_lines(self, order_source, original_lines):
        lines = []
        shop = order_source.shop
        for product in self.products.all():
            shop_product = product.get_shop_instance(shop)
            supplier = shop_product.suppliers.first()
            if not shop_product.is_orderable(
                    supplier=supplier, customer=order_source.customer, quantity=1):
                continue
            line_data = dict(
                line_id="free_product_%s" % str(random.randint(0, 0x7FFFFFFF)),
                type=OrderLineType.PRODUCT,
                quantity=self.quantity,
                shop=shop,
                text=("%s (%s)" % (product.name, self.campaign.public_name)),
                base_unit_price=shop.create_price(0),
                product=product,
                sku=product.sku,
                supplier=supplier,
                line_source=LineSource.DISCOUNT_MODULE
            )
            lines.append(order_source.create_line(**line_data))
        return lines


class DiscountFromProduct(BasketLineEffect):
    identifier = "discount_from_product_line_effect"
    model = Product
    name = _("Discount from Product")

    per_line_discount = models.BooleanField(
        default=True,
        verbose_name=_("per line discount"),
        help_text=_("Uncheck this if you want to give discount for each matched product."))

    discount_amount = MoneyValueField(
        default=None, blank=True, null=True,
        verbose_name=_("discount amount"),
        help_text=_("Flat amount of discount."))

    products = models.ManyToManyField(Product, verbose_name=_("product"))

    @property
    def description(self):
        return _("Select discount amount and products.")

    def get_discount_lines(self, order_source, original_lines):
        product_ids = self.products.values_list("pk", flat=True)
        for line in original_lines:
            if not line.type == OrderLineType.PRODUCT:
                continue
            if line.product.pk not in product_ids:
                continue
            amnt = (self.discount_amount * line.quantity) if not self.per_line_discount else self.discount_amount
            discount_price = order_source.create_price(amnt)
            if not line.discount_amount or line.discount_amount < discount_price:
                line.discount_amount = discount_price
        return []


class DiscountFromCategoryProducts(BasketLineEffect):
    identifier = "discount_from_category_products_line_effect"
    model = Category
    name = _("Discount from Category products")

    discount_amount = MoneyValueField(
        default=None, blank=True, null=True,
        verbose_name=_("discount amount"),
        help_text=_("Flat amount of discount."))
    discount_percentage = models.DecimalField(
        max_digits=6, decimal_places=5, blank=True, null=True,
        verbose_name=_("discount percentage"),
        help_text=_("The discount percentage for this campaign."))
    category = models.ForeignKey(Category, verbose_name=_("category"))

    @property
    def description(self):
        return _(
            'Select discount amount and category. '
            'Please note that the discount will be given to all matching products in basket.')

    def get_discount_lines(self, order_source, original_lines):
        if not (self.discount_percentage or self.discount_amount):
            return []

        product_ids = self.category.shop_products.values_list("product_id", flat=True)
        for line in original_lines:  # Use original lines since we don't want to discount free product lines
            if not line.type == OrderLineType.PRODUCT:
                continue
            if line.product.pk not in product_ids:
                continue

            if self.discount_amount:
                amount = self.discount_amount * line.quantity
                discount_price = order_source.create_price(amount)
            elif self.discount_percentage:
                amount = line.taxless_price * self.discount_percentage
                discount_price = order_source.create_price(amount)

            if not line.discount_amount or line.discount_amount < discount_price:
                line.discount_amount = discount_price

        return []
