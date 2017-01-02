# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.db.models import Q

from shuup.core.models import Order


class OrderReportMixin(object):
    def get_objects(self):
        queryset = Order.objects.filter(
            shop=self.shop,
            order_date__range=(self.start_date, self.end_date))
        creator = self.options.get("creator")
        orderer = self.options.get("orderer")
        customer = self.options.get("customer")
        filters = Q()
        if creator:
            filters &= Q(creator__in=creator)
        if orderer:
            filters &= Q(orderer__in=orderer)
        if customer:
            filters &= Q(customer__in=customer)

        return queryset.filter(filters).valid().paid().order_by("order_date")
