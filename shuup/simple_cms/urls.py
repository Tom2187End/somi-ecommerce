# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import url

from shuup.simple_cms.views import PageView

urlpatterns = [
    url(r'^(?P<url>.*)/$',
        PageView.as_view(),
        name='cms_page'),
]
