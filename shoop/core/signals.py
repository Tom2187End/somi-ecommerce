# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.dispatch import Signal

get_visibility_errors = Signal(providing_args=["shop_product", "customer"], use_caching=True)
get_orderability_errors = Signal(providing_args=["shop_product", "customer", "supplier", "quantity"], use_caching=True)
