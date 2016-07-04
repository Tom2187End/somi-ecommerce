# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from jsonfield import JSONField

from shuup.core.fields import MoneyValueField, QuantityField, UnsavedForeignKey
from shuup.core.pricing import Priceful
from shuup.core.taxing import LineTax
from shuup.utils.money import Money
from shuup.utils.properties import MoneyProperty, MoneyPropped, PriceProperty

from ._base import ShuupModel


class OrderLineType(Enum):
    PRODUCT = 1
    SHIPPING = 2
    PAYMENT = 3
    DISCOUNT = 4
    OTHER = 5
    REFUND = 6
    ROUNDING = 7

    class Labels:
        PRODUCT = _('product')
        SHIPPING = _('shipping')
        PAYMENT = _('payment')
        DISCOUNT = _('discount')
        OTHER = _('other')
        REFUND = _('refund')
        ROUNDING = _('rounding')


class OrderLineManager(models.Manager):

    def products(self):  # pragma: no cover
        return self.filter(type=OrderLineType.PRODUCT)

    def shipping(self):  # pragma: no cover
        return self.filter(type=OrderLineType.SHIPPING)

    def payment(self):  # pragma: no cover
        return self.filter(type=OrderLineType.PAYMENT)

    def discounts(self):
        return self.filter(type=OrderLineType.DISCOUNT)

    def refunds(self):
        return self.filter(type=OrderLineType.REFUND)

    def other(self):  # pragma: no cover
        return self.filter(type=OrderLineType.OTHER)


@python_2_unicode_compatible
class OrderLine(MoneyPropped, models.Model, Priceful):
    order = UnsavedForeignKey("Order", related_name='lines', on_delete=models.PROTECT, verbose_name=_('order'))
    product = UnsavedForeignKey(
        "Product", blank=True, null=True, related_name="order_lines",
        on_delete=models.PROTECT, verbose_name=_('product')
    )
    supplier = UnsavedForeignKey(
        "Supplier", blank=True, null=True, related_name="order_lines",
        on_delete=models.PROTECT, verbose_name=_('supplier')
    )

    parent_line = UnsavedForeignKey(
        "self", related_name="child_lines", blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('parent line')
    )
    ordering = models.IntegerField(default=0, verbose_name=_('ordering'))
    type = EnumIntegerField(OrderLineType, default=OrderLineType.PRODUCT, verbose_name=_('line type'))
    sku = models.CharField(max_length=48, blank=True, verbose_name=_('line SKU'))
    text = models.CharField(max_length=256, verbose_name=_('line text'))
    accounting_identifier = models.CharField(max_length=32, blank=True, verbose_name=_('accounting identifier'))
    require_verification = models.BooleanField(default=False, verbose_name=_('require verification'))
    verified = models.BooleanField(default=False, verbose_name=_('verified'))
    extra_data = JSONField(blank=True, null=True, verbose_name=_('extra data'))

    # The following fields govern calculation of the prices
    quantity = QuantityField(verbose_name=_('quantity'), default=1)
    base_unit_price = PriceProperty('base_unit_price_value', 'order.currency', 'order.prices_include_tax')
    discount_amount = PriceProperty('discount_amount_value', 'order.currency', 'order.prices_include_tax')

    base_unit_price_value = MoneyValueField(verbose_name=_('unit price amount (undiscounted)'), default=0)
    discount_amount_value = MoneyValueField(verbose_name=_('total amount of discount'), default=0)

    objects = OrderLineManager()

    class Meta:
        verbose_name = _('order line')
        verbose_name_plural = _('order lines')

    def __str__(self):
        return "%dx %s (%s)" % (self.quantity, self.text, self.get_type_display())

    @property
    def tax_amount(self):
        """
        :rtype: shuup.utils.money.Money
        """
        zero = Money(0, self.order.currency)
        return sum((x.amount for x in self.taxes.all()), zero)

    @property
    def max_refundable_amount(self):
        """
        :rtype: shuup.utils.money.Money
        """
        refunds = self.order.lines.refunds().filter(parent_line=self)
        refund_total_value = sum(refund.taxful_price.amount.value for refund in refunds)
        return (self.taxful_price.amount + Money(refund_total_value, self.order.currency))

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = u""
        if self.type == OrderLineType.PRODUCT and not self.product_id:
            raise ValidationError("Product-type order line can not be saved without a set product")

        if self.product_id and self.type != OrderLineType.PRODUCT:
            raise ValidationError("Order line has product but is not of Product type")

        if self.product_id and not self.supplier_id:
            raise ValidationError("Order line has product but no supplier")

        super(OrderLine, self).save(*args, **kwargs)
        if self.product_id:
            self.supplier.module.update_stock(self.product_id)


@python_2_unicode_compatible
class OrderLineTax(MoneyPropped, ShuupModel, LineTax):
    order_line = models.ForeignKey(
        OrderLine, related_name='taxes', on_delete=models.PROTECT,
        verbose_name=_('order line'))
    tax = models.ForeignKey(
        "Tax", related_name="order_line_taxes",
        on_delete=models.PROTECT, verbose_name=_('tax'))
    name = models.CharField(max_length=200, verbose_name=_('tax name'))

    amount = MoneyProperty('amount_value', 'order_line.order.currency')
    base_amount = MoneyProperty('base_amount_value', 'order_line.order.currency')

    amount_value = MoneyValueField(verbose_name=_('tax amount'))
    base_amount_value = MoneyValueField(
        verbose_name=_('base amount'),
        help_text=_('Amount that this tax is calculated from'))

    ordering = models.IntegerField(default=0, verbose_name=_('ordering'))

    class Meta:
        ordering = ["ordering"]

    def __str__(self):
        return "%s: %s on %s" % (self.name, self.amount, self.base_amount)
