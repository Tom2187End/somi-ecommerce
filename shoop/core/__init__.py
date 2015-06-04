# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps import AppConfig


class ShoopCoreAppConfig(AppConfig):
    name = "shoop.core"
    verbose_name = "Shoop Core"
    label = "shoop"  # Use "shoop" as app_label instead of "core"


default_app_config = "shoop.core.ShoopCoreAppConfig"
