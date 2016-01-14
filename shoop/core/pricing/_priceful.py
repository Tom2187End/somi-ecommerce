# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import decimal

from ._price import TaxfulPrice, TaxlessPrice
from ._priceful_properties import TaxfulFrom, TaxlessFrom


class Priceful(object):
    """
    Mixin to define price properties based on other price properties.

    You must provide at least

     * ``quantity`` (`~decimal.Decimal`)

    and both

     * ``base_unit_price`` (`~shoop.core.pricing.Price`) and
     * ``discount_amount`` (`~shoop.core.pricing.Price`)

    or both

     * ``price`` (`~shoop.core.pricing.Price`) and
     * ``base_price`` (`~shoop.core.pricing.Price`).

    You may also provide

     * ``tax_amount`` (`~shoop.utils.money.Money`)

    to get various tax related properties.

    Provided ``base_unit_price``, ``discount_amount``, ``price``,
    ``base_price``, and ``tax_amount`` must have compatible units
    (i.e. same taxness and currency).

    Invariants:
      * ``price = base_unit_price * quantity - discount_amount``
      * ``discount_amount = base_price - price``
      * ``discount_rate = 1 - (price / base_price)``
      * ``discount_percentage = 100 * discount_rate``
      * ``unit_discount_amount = discount_amount / quantity``
      * ``taxful_price = taxless_price + tax_amount``
      * ``tax_rate = (taxful_price.amount / taxless_price.amount) - 1``
      * ``tax_percentage = 100 * tax_rate``
    """
    @property
    def price(self):
        """
        Total price for the specified quantity with discount.

        :rtype: shoop.core.pricing.Price
        """
        return self.base_unit_price * self.quantity - self.discount_amount

    @property
    def base_price(self):
        """
        Total price for the specified quantity excluding discount.

        :rtype: shoop.core.pricing.Price
        """
        return self.price + self.discount_amount

    @property
    def base_unit_price(self):
        """
        Undiscounted unit price.

        Note: If quantity is 0, will return ``base_price``.

        :rtype: shoop.core.pricing.Price
        """
        return self.base_price / (self.quantity or 1)

    @property
    def discount_amount(self):
        """
        Amount of discount for the total quantity.

        :rtype: shoop.core.pricing.Price
        """
        return (self.base_price - self.price)

    @property
    def discount_rate(self):
        """
        Discount rate, 1 meaning totally discounted.

        Note: Could be negative, when base price is smaller than
        effective price.  Could also be greater than 1, when effective
        price is negative.

        If base price is 0, will return 0.

        :rtype: decimal.Decimal
        """
        if not self.base_price:
            return decimal.Decimal(0)
        return 1 - (self.price / self.base_price)

    @property
    def discount_percentage(self):
        """
        Discount percentage, 100 meaning totally discounted.

        See `discount_rate`.

        :rtype: decimal.Decimal
        """
        return self.discount_rate * 100

    @property
    def is_discounted(self):
        """
        Check if there is a discount in effect.

        :return: True, iff price < base price.
        """
        return (self.price < self.base_price)

    @property
    def discounted_unit_price(self):
        """
        Unit price with discount.

        If quantity is 0, will return ``base_unit_price - discount_amount``.

        :rtype: shoop.core.pricing.Price
        """
        return self.base_unit_price - (self.discount_amount / (self.quantity or 1))

    @property
    def unit_discount_amount(self):
        """
        Discount amount per unit.

        If quantity is 0, will return ``discount_amount``.

        :rtype: shoop.core.pricing.Price
        """
        return self.discount_amount / (self.quantity or 1)

    @property
    def tax_rate(self):
        """
        :rtype: decimal.Decimal
        """
        taxless = self.taxless_price
        taxful = self.taxful_price
        if not taxless.amount:
            return decimal.Decimal(0)
        return (taxful.amount / taxless.amount) - 1

    @property
    def tax_percentage(self):
        """
        :rtype: decimal.Decimal
        """
        return self.tax_rate * 100

    @property
    def taxful_price(self):
        """
        :rtype: TaxfulPrice
        """
        price = self.price
        if price.includes_tax:
            return price
        else:
            return TaxfulPrice(price.amount + self.tax_amount)

    @property
    def taxless_price(self):
        """
        :rtype: TaxlessPrice
        """
        price = self.price
        if price.includes_tax:
            return TaxlessPrice(price.amount - self.tax_amount)
        else:
            return price

    taxful_base_price = TaxfulFrom('base_price')
    taxless_base_price = TaxlessFrom('base_price')

    taxful_discount_amount = TaxfulFrom('discount_amount')
    taxless_discount_amount = TaxlessFrom('discount_amount')

    taxful_base_unit_price = TaxfulFrom('base_unit_price')
    taxless_base_unit_price = TaxlessFrom('base_unit_price')

    taxful_discounted_unit_price = TaxfulFrom('discounted_unit_price')
    taxless_discounted_unit_price = TaxlessFrom('discounted_unit_price')

    taxful_unit_discount_amount = TaxfulFrom('unit_discount_amount')
    taxless_unit_discount_amount = TaxlessFrom('unit_discount_amount')
