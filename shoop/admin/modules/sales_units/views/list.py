# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shoop.admin.utils.picotable import Column, TextFilter
from shoop.admin.utils.views import PicotableListView
from shoop.core.models import SalesUnit


class SalesUnitListView(PicotableListView):
    model = SalesUnit
    columns = [
        Column("name", _(u"Name"), sort_field="translations__name", display="name", filter_config=TextFilter(
            filter_field="translations__name",
            placeholder=_("Filter by name...")
        )),
        Column("short_name", _(u"Short Name"), sort_field="translations__short_name", display="short_name"),
        Column("decimals", _(u"Allowed decimals")),
    ]

    def get_queryset(self):
        return SalesUnit.objects.all()
