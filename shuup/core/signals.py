# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.dispatch import Signal

get_visibility_errors = Signal(providing_args=["shop_product", "customer"], use_caching=True)
get_orderability_errors = Signal(providing_args=["shop_product", "customer", "supplier", "quantity"], use_caching=True)
shipment_created = Signal(providing_args=["order", "shipment"], use_caching=True)
refund_created = Signal(providing_args=["order", "refund_lines"], use_caching=True)
