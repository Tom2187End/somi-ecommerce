# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(
    '',
    url(r'^order-history/$', views.OrderListView.as_view(),
        name='personal-orders'),
    url(r'^order-history/(?P<pk>.+)/$', views.OrderDetailView.as_view(),
        name='show-order'),
)
