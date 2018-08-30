# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import django

from ._auth import EmailAuthenticationForm
from ._base import ShuupAdminForm, ShuupAdminFormNoTranslation

if django.VERSION < (1, 11):
    from ._quick_select import (
        QuickAddRelatedObjectMultiSelectWithoutTemplate as QuickAddRelatedObjectMultiSelect,
        QuickAddRelatedObjectSelectWithoutTemplate as QuickAddRelatedObjectSelect
    )
else:
    from ._quick_select import (
        QuickAddRelatedObjectMultiSelect, QuickAddRelatedObjectSelect
    )


__all__ = [
    "EmailAuthenticationForm",
    "ShuupAdminForm",
    "ShuupAdminFormNoTranslation",
    "QuickAddRelatedObjectMultiSelect",
    "QuickAddRelatedObjectSelect"
]
