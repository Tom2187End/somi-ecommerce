# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup.apps import AppConfig


class SimpleSearchAppConfig(AppConfig):
    name = "shuup.front.apps.simple_search"
    verbose_name = "Shuup Frontend - Simple Search"
    label = "shuup_front.simple_search"

    provides = {
        "front_urls": [
            "shuup.front.apps.simple_search.urls:urlpatterns"
        ],
        "front_template_helper_namespace": [
            "shuup.front.apps.simple_search.template_helpers:TemplateHelpers"
        ]
    }


default_app_config = "shuup.front.apps.simple_search.SimpleSearchAppConfig"
