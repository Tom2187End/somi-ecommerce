# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from ._delete import ServiceProviderDeleteView
from ._edit import ServiceProviderEditView
from ._list import ServiceProviderListView

__all__ = [
    "ServiceProviderDeleteView",
    "ServiceProviderEditView",
    "ServiceProviderListView",
]
