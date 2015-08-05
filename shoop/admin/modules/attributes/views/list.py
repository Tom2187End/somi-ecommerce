# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _
from shoop.admin.utils.picotable import Column, TextFilter, ChoicesFilter
from shoop.admin.utils.views import PicotableListView
from shoop.core.models import Attribute
from shoop.core.models.attributes import AttributeType, AttributeVisibility


class AttributeListView(PicotableListView):
    model = Attribute
    columns = [
        Column("identifier", _("Identifier"), filter_config=TextFilter(
            filter_field="identifier",
            placeholder=_("Filter by identifier...")
        )),
        Column("name", _("Name"), sort_field="translations__name", display="name", filter_config=TextFilter(
            filter_field="translations__name",
            placeholder=_("Filter by name...")
        )),
        Column("type", _("Type"), filter_config=ChoicesFilter(AttributeType.choices)),
        Column("visibility_mode", _("Visibility Mode"), filter_config=ChoicesFilter(AttributeVisibility.choices)),
        Column("searchable", _("Searchable")),
        Column("n_product_types", _("Used in # Product Types")),
    ]

    def get_queryset(self):
        return Attribute.objects.all().annotate(n_product_types=Count("product_types"))
