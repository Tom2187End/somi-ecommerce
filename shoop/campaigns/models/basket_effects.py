# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.db import models
from django.utils.translation import ugettext_lazy as _

from shoop.admin.forms.fields import PercentageField
from shoop.core.fields import MoneyValueField
from shoop.core.models import PolymorphicShoopModel


class BasketDiscountEffect(PolymorphicShoopModel):
    identifier = None
    model = None
    admin_form_class = None

    campaign = models.ForeignKey("BasketCampaign", related_name='effects', verbose_name=_("campaign"))

    def apply_for_basket(self, order_source):
        """
        Applies the effect based on given `order_source`

        :return: amount of discount to accumulate for the product
        :rtype: Price
        """
        raise NotImplementedError("Not implemented!")


class BasketDiscountAmount(BasketDiscountEffect):
    identifier = "discount_amount_effect"
    name = _("Discount amount value")

    discount_amount = MoneyValueField(
        default=None, blank=True, null=True,
        verbose_name=_("discount amount"),
        help_text=_("Flat amount of discount."))

    @property
    def description(self):
        return _("Give discount amount.")

    @property
    def value(self):
        return self.discount_amount

    @value.setter
    def value(self, value):
        self.discount_amount = value

    def apply_for_basket(self, order_source):
        return order_source.create_price(self.value)


class BasketDiscountPercentage(BasketDiscountEffect):
    identifier = "discount_percentage_effect"
    name = _("Discount amount percentage")
    admin_form_class = PercentageField

    discount_percentage = models.DecimalField(
        max_digits=6, decimal_places=5, blank=True, null=True,
        verbose_name=_("discount percentage"),
        help_text=_("The discount percentage for this campaign."))

    @property
    def description(self):
        return _("Give percentage discount.")

    @property
    def value(self):
        return self.discount_percentage

    @value.setter
    def value(self, value):
        self.discount_percentage = value

    def apply_for_basket(self, order_source):
        return (order_source.total_price_of_products * self.value)
