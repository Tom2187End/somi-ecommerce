# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.admin.forms.fields import WeekdayField
from shuup.admin.forms.widgets import TimeInput
from shuup.campaigns.models.basket_conditions import (
    BasketMaxTotalAmountCondition, BasketMaxTotalProductAmountCondition,
    BasketTotalAmountCondition, BasketTotalProductAmountCondition,
    CategoryProductsBasketCondition, ContactBasketCondition,
    ContactGroupBasketCondition, HourBasketCondition,
    ProductsInBasketCondition
)
from shuup.core.models import Category

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


class CategoryProductsBasketConditionForm(BaseRuleModelForm):
    def __init__(self, **kwargs):
        super(CategoryProductsBasketConditionForm, self).__init__(**kwargs)
        self.fields["categories"].queryset = Category.objects.all_except_deleted()
        self.fields["excluded_categories"].queryset = Category.objects.all_except_deleted()

    class Meta(BaseRuleModelForm.Meta):
        model = CategoryProductsBasketCondition


class HourBasketConditionForm(BaseRuleModelForm):
    days = WeekdayField()

    class Meta(BaseRuleModelForm.Meta):
        model = HourBasketCondition
        widgets = {
            "hour_start": TimeInput(),
            "hour_end": TimeInput(),
        }

    def __init__(self, **kwargs):
        super(HourBasketConditionForm, self).__init__(**kwargs)

        if self.instance:
            self.fields["days"].initial = self.instance.days.split(",")
