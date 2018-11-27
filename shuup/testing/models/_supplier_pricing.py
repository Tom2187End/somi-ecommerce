# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models

from shuup.core.fields import MoneyValueField
from shuup.utils.properties import MoneyPropped, PriceProperty


class SupplierPrice(MoneyPropped, models.Model):
    shop = models.ForeignKey("shuup.Shop")
    supplier = models.ForeignKey("shuup.Supplier")
    product = models.ForeignKey("shuup.Product")
    amount_value = MoneyValueField()
    amount = PriceProperty("amount_value", "shop.currency", "shop.prices_include_tax")
