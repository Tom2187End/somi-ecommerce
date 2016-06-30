# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from shuup.admin.forms import ShuupAdminForm
from shuup.core.models import CustomCarrier, CustomPaymentProcessor


class CustomCarrierForm(ShuupAdminForm):
    class Meta:
        model = CustomCarrier
        exclude = ("identifier", )


class CustomPaymentProcessorForm(ShuupAdminForm):
    class Meta:
        model = CustomPaymentProcessor
        exclude = ("identifier", )
