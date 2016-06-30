# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.admin.dashboard import DashboardNumberBlock
from shuup.core.models import Order


def get_active_customers_block(request):
    customer_ids = set(Order.objects.since(30).values_list("customer_id", flat=True))

    return DashboardNumberBlock(
        id="active_customers_count",
        color="blue",
        title=_("Active customers"),
        value=len(customer_ids),
        icon="fa fa-history",
        subtitle=_("Based on orders within 30 days")
    )
