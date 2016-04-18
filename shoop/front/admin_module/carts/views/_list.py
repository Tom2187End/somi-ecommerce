# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime

from babel.dates import format_datetime
from django.utils.html import escape
from django.utils.timezone import localtime, now
from django.utils.translation import ugettext as _

from shoop.admin.utils.picotable import (
    ChoicesFilter, Column, DateRangeFilter, MultiFieldTextFilter, RangeFilter
)
from shoop.admin.utils.views import PicotableListView
from shoop.core.models import Shop
from shoop.front.models import StoredBasket
from shoop.utils.i18n import format_money, get_current_babel_locale


class CartListView(PicotableListView):
    model = StoredBasket
    columns = [
        Column("created_on", _(u"Created on"), display="format_created_date", filter_config=DateRangeFilter()),
        Column("updated_on", _(u"Last updated on"), display="format_updated_date", filter_config=DateRangeFilter()),
        Column(
            "finished", _("Abandoned"),
            display="format_abandoned_status",
            filter_config=ChoicesFilter([(False, _("yes")), (True, _("no"))])
        ),
        Column("shop", _("Shop"), filter_config=ChoicesFilter(choices=Shop.objects.all())),
        Column("product_count", _("Product count"), filter_config=RangeFilter()),
        Column(
            "customer", _(u"Customer"),
            filter_config=MultiFieldTextFilter(filter_fields=("customer__email", "customer__name"))
        ),
        Column(
            "orderer", _(u"Orderer"),
            filter_config=MultiFieldTextFilter(filter_fields=("orderer__email", "orderer__name"))
        ),
        Column(
            "taxful_total_price", _(u"Total"), sort_field="taxful_total_price_value",
            display="format_taxful_total_price", class_name="text-right",
            filter_config=RangeFilter(field_type="number", filter_field="taxful_total_price_value")
        ),
    ]

    def get_queryset(self):
        """
        Ignore potentially active carts, displaying only those not updated for at least 2 hours.
        """
        cutoff = now() - datetime.timedelta(hours=2)
        filters = {"updated_on__lt": cutoff, "product_count__gte": 0}
        return super(CartListView, self).get_queryset().filter(**filters)

    def format_abandoned_status(self, instance, *args, **kwargs):
        return "yes" if not instance.finished else "no"

    def format_created_date(self, instance, *args, **kwargs):
        return format_datetime(localtime(instance.created_on), locale=get_current_babel_locale())

    def format_updated_date(self, instance, *args, **kwargs):
        return format_datetime(localtime(instance.updated_on), locale=get_current_babel_locale())

    def format_taxful_total_price(self, instance, *args, **kwargs):
        return escape(format_money(instance.taxful_total_price))

    def get_context_data(self, **kwargs):
        context = super(CartListView, self).get_context_data(**kwargs)
        context["title"] = _("Carts")
        return context

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Created on"), "text": item["created_on"]},
            {"title": _(u"Last updated on"), "text": item["updated_on"]},
            {"title": _(u"Ordered"), "text": item["finished"]},
            {"title": _(u"Total"), "text": item["taxful_total_price"]},
        ]
