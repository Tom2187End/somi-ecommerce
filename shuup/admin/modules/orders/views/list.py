# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, DateRangeFilter, MultiFieldTextFilter, RangeFilter,
    TextFilter
)
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import (
    Order, OrderStatus, OrderStatusRole, PaymentStatus, ShippingStatus
)
from shuup.utils.i18n import format_money, get_locally_formatted_datetime


class OrderStatusChoicesFilter(ChoicesFilter):
    """
    Custom choices filter for order statuses

    Sets filter default choice to initial order status if status
    exists. Default order status can not be passed for init
    since it would cause database queries and in all cases
    the order status table might not even be in the database
    when init is called.
    """
    @property
    def default(self):
        return getattr(OrderStatus.objects.filter(role=OrderStatusRole.INITIAL).first(), "pk", None)

    @default.setter
    def default(self, value):
        pass


class OrderListView(PicotableListView):
    model = Order
    default_columns = [
        Column("identifier", _(u"Order"), linked=True, filter_config=TextFilter(operator="startswith")),
        Column("order_date", _(u"Order Date"), display="format_order_date", filter_config=DateRangeFilter()),
        Column(
            "customer", _(u"Customer"), display="format_customer_name",
            filter_config=MultiFieldTextFilter(
                filter_fields=(
                    "customer__email", "customer__name", "billing_address__name",
                    "shipping_address__name", "orderer__name"
                )
            )
        ),
        Column(
            "status", _(u"Status"), filter_config=OrderStatusChoicesFilter(choices=OrderStatus.objects.all()),
        ),
        Column("payment_status", _(u"Payment Status"), filter_config=ChoicesFilter(choices=PaymentStatus.choices)),
        Column("shipping_status", _(u"Shipping Status"), filter_config=ChoicesFilter(choices=ShippingStatus.choices)),
        Column(
            "taxful_total_price_value", _(u"Total"), sort_field="taxful_total_price_value",
            display="format_taxful_total_price", class_name="text-right",
            filter_config=RangeFilter(field_type="number", filter_field="taxful_total_price_value")
        ),
    ]
    mass_actions = [
        "shuup.admin.modules.orders.mass_actions:CancelOrderAction",
        "shuup.admin.modules.orders.mass_actions:OrderConfirmationPdfAction",
        "shuup.admin.modules.orders.mass_actions:OrderDeliveryPdfAction",
    ]

    def get_queryset(self):
        qs = super(OrderListView, self).get_queryset().exclude(deleted=True)
        if not self.request.user.is_superuser:
            shop = get_shop(self.request)
            qs = qs.filter(shop=shop)
        return qs

    def format_customer_name(self, instance, *args, **kwargs):
        return instance.get_customer_name() or ""

    def format_order_date(self, instance, *args, **kwargs):
        return get_locally_formatted_datetime(instance.order_date)

    def format_taxful_total_price(self, instance, *args, **kwargs):
        return escape(format_money(instance.taxful_total_price))

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Total"), "text": item.get("taxful_total_price_value")},
            {"title": _(u"Status"), "text": item.get("status")}
        ]
