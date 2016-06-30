# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.campaigns.models.basket_conditions import (
    BasketMaxTotalAmountCondition, BasketMaxTotalProductAmountCondition,
    BasketTotalAmountCondition, BasketTotalProductAmountCondition,
    ContactBasketCondition, ContactGroupBasketCondition,
    ProductsInBasketCondition
)

from ._base import BaseRuleModelForm


class BasketTotalProductAmountConditionForm(BaseRuleModelForm):
    class Meta(BaseRuleModelForm.Meta):
        model = BasketTotalProductAmountCondition


class BasketTotalAmountConditionForm(BaseRuleModelForm):
    class Meta(BaseRuleModelForm.Meta):
        model = BasketTotalAmountCondition


class ProductsInBasketConditionForm(BaseRuleModelForm):
    class Meta(BaseRuleModelForm.Meta):
        model = ProductsInBasketCondition


class ContactGroupBasketConditionForm(BaseRuleModelForm):
    class Meta(BaseRuleModelForm.Meta):
        model = ContactGroupBasketCondition


class ContactBasketConditionForm(BaseRuleModelForm):
    class Meta(BaseRuleModelForm.Meta):
        model = ContactBasketCondition


class BasketMaxTotalProductAmountConditionForm(BaseRuleModelForm):
    class Meta(BaseRuleModelForm.Meta):
        model = BasketMaxTotalProductAmountCondition


class BasketMaxTotalAmountConditionForm(BaseRuleModelForm):
    class Meta(BaseRuleModelForm.Meta):
        model = BasketMaxTotalAmountCondition
