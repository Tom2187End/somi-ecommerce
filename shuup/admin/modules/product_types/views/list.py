# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db.models import Count
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import Column, TextFilter
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import ProductType


class ProductTypeListView(PicotableListView):
    model = ProductType
    default_columns = [
        Column(
            "name",
            _(u"Name"),
            sort_field="translations__name",
            display="name",
            filter_config=TextFilter(filter_field="translations__name", placeholder=_("Filter by name..."))),
        Column("n_attributes", _(u"Number of Attributes")),
    ]

    def get_queryset(self):
        return ProductType.objects.all().annotate(n_attributes=Count("attributes"))
