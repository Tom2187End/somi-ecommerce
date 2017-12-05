# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from rest_framework import serializers

from shuup.api.fields import FormattedDecimalField


class BaseLineSerializerMixin(serializers.Serializer):
    quantity = FormattedDecimalField()
    price = FormattedDecimalField()
    base_price = FormattedDecimalField()
    discount_amount = FormattedDecimalField()
    discounted_unit_price = FormattedDecimalField()
    is_discounted = serializers.BooleanField()


class TaxLineSerializerMixin(serializers.Serializer):
    taxful_base_unit_price = FormattedDecimalField()
    taxful_discount_amount = FormattedDecimalField()
    taxful_price = FormattedDecimalField()
    taxful_discounted_unit_price = FormattedDecimalField()

    taxless_base_unit_price = FormattedDecimalField()
    taxless_discount_amount = FormattedDecimalField()
    taxless_price = FormattedDecimalField()
    taxless_discounted_unit_price = FormattedDecimalField()

    tax_amount = FormattedDecimalField()


class BaseOrderTotalSerializerMixin(serializers.Serializer):
    taxful_total_price = FormattedDecimalField()
    taxless_total_price = FormattedDecimalField()
    prices_include_tax = serializers.BooleanField()
