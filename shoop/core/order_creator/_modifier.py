# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.transaction import atomic
from django.utils.timezone import now

from shoop.core.models import Order
from shoop.core.utils.users import real_user_or_none

from ._creator import OrderProcessor
from ._source_modifier import get_order_source_modifier_modules


class OrderModifier(OrderProcessor):

    _PROTECTED_ATTRIBUTES = [
        "shop",
        "currency,"
        "prices_include_tax",
        "creator",
        "created_on",
        "ip_address"
    ]

    @atomic
    def update_order_from_source(self, order_source, order):
        data = self.get_source_base_data(order_source)
        for key in self._PROTECTED_ATTRIBUTES:
            if key in data:
                data.pop(key)
        data.update({
            "modified_by": real_user_or_none(order_source.modified_by),
            "modified_on": now()
        })
        Order.objects.filter(pk=order.pk).update(**data)

        order = Order.objects.get(pk=order.pk)
        for module in get_order_source_modifier_modules():
            module.clear_codes(order)

        for line in order.lines.all():
            line.taxes.all().delete()  # Delete all tax lines before OrderLine's
            line.delete()

        return self.finalize_creation(order, order_source)
