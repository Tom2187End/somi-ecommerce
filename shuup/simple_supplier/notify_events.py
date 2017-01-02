# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from time import time

from django.utils.translation import ugettext_lazy as _

from shuup.core import cache
from shuup.notify.base import Event, Variable
from shuup.notify.typology import Boolean, Model


class AlertLimitReached(Event):
    cache_key_fmt = "stock_alert_%s_%s"

    identifier = "alert_limit_reached"
    name = _("Alert Limit Reached")

    supplier = Variable(_("Supplier"), type=Model("shuup.Supplier"))
    product = Variable(_("Product"), type=Model("shuup.Product"))
    dispatched_last_24hs = Variable(_("Dispatched last 24 hours"),
                                    type=Boolean,
                                    help_text=_("This will be True if this event was already dispatched "
                                                "in the last 24 hours for the same product and supplier. "
                                                "This is useful to prevent sending identical notifications in a short "
                                                "period of time."))

    def __init__(self, **variable_values):
        cache_key = self.cache_key_fmt % (variable_values["supplier"].pk, variable_values["product"].pk)
        last_dispatch_time = cache.get(cache_key)

        if last_dispatch_time:
            last_dispatch = int((time() - last_dispatch_time) / 60 / 60)
            variable_values["dispatched_last_24hs"] = (last_dispatch < 24)
        else:
            variable_values["dispatched_last_24hs"] = False

        super(AlertLimitReached, self).__init__(**variable_values)

    def run(self):
        cache_key = self.cache_key_fmt % (self.variable_values["supplier"].pk, self.variable_values["product"].pk)
        cache.set(cache_key, time(), timeout=(60 * 60 * 24))
        super(AlertLimitReached, self).run()
