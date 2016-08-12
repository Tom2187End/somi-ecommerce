# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from collections import OrderedDict
from decimal import Decimal

import six
from django.utils.encoding import force_text
from django.utils.functional import Promise

from shuup.apps.provides import get_provide_objects
from shuup.core.models import Shop
from shuup.core.pricing import TaxfulPrice, TaxlessPrice
from shuup.reports.forms import BaseReportForm
from shuup.reports.utils import parse_date_range


class ShuupReportBase(object):
    filename_template = None
    icon = "fa-money"

    form_class = BaseReportForm

    def __init__(self, **kwargs):
        if kwargs.get("initial"):
            self.options = kwargs["initial"]
        else:
            self.options = kwargs
        self.start_date = None
        self.end_date = None
        if self.options.get("date_range"):
            self.start_date, self.end_date = parse_date_range(self.options["date_range"])
        if self.options.get("shop"):
            self.shop = Shop.objects.get(pk=self.options["shop"])
        else:
            self.shop = None
        self.rendered = False

    def __unicode__(self):
        return self.title

    @classmethod
    def get_name(cls):
        return cls.identifier

    @classmethod
    def get_title(cls):
        return force_text(cls.title)

    def ensure_texts(self):
        """
        Ensure that lazy objects are forced as texts
        """
        s = []
        for row in self.schema:
            if isinstance(row["title"], Promise):
                row["title"] = force_text(row["title"])
            s.append(row)
        self.schema = s

    def get_return_data(self, data, has_totals=True):
        return {
            "start": self.start_date,
            "end": self.end_date,
            "data": data,
            "has_totals": has_totals
        }

    def dict_getter(self, c, datum):
        return datum.get(c["key"])

    def cls_getter(self, c, datum):
        return getattr(datum, c["key"], None)

    def read_datum(self, datum):
        if isinstance(datum, dict):
            getter = self.dict_getter
        else:
            getter = self.cls_getter
        return [(c["getter"] if callable(c.get("getter")) else getter)(c, datum) for c in self.schema]

    def get_totals(self, data):
        price_types = [TaxlessPrice, TaxfulPrice]
        simple_types = [int, float, Decimal]
        countable_types = price_types + simple_types
        totals = {}
        for datum in data:
            for c, val in zip(self.schema, self.read_datum(datum)):
                k = c["key"]
                if k not in totals:
                    if type(val) in price_types or type(val) in simple_types:
                        cls = type(val)
                        if type(val) in price_types:
                            totals[k] = cls(0, currency=self.shop.currency)
                        else:
                            totals[k] = cls(0)
                    else:
                        totals[k] = None

                if type(val) in countable_types:
                    totals[k] += val

        return totals


def get_report_class(name):
    for cls_name, cls in six.iteritems(get_report_classes()):
        if cls_name == name:
            return cls
    return None


def get_report_classes():
    items = {}
    for cls in list(get_provide_objects("reports")):
        items[cls.get_name()] = cls
    return OrderedDict(sorted(items.items(), key=lambda t: t[1].title))
