# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.utils import update_module_attributes

from ._theme import override_current_theme_class

__all__ = [
    "override_current_theme_class",
]

update_module_attributes(__all__, __name__)
