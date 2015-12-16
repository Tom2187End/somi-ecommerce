# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from .edit import CustomerTaxGroupEditView, TaxClassEditView, TaxEditView
from .list import CustomerTaxGroupListView, TaxClassListView, TaxListView

__all__ = [
    "TaxClassListView", "TaxClassEditView",
    "TaxEditView", "TaxListView",
    "CustomerTaxGroupEditView", "CustomerTaxGroupListView"
]
