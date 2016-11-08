# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from itertools import chain

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.i18n import set_language

from shuup.apps.provides import get_provide_objects
from shuup.utils.i18n import javascript_catalog_all

from .views.basket import BasketView
from .views.category import CategoryView
from .views.checkout import get_checkout_view
from .views.dashboard import DashboardView
from .views.index import IndexView
from .views.misc import toggle_all_seeing
from .views.order import OrderCompleteView
from .views.payment import ProcessPaymentView
from .views.product import ProductDetailView


# TODO: Check _not_here_yet URLs in this file


def _not_here_yet(request, *args, **kwargs):
    return HttpResponse(
        "Not here yet: %s (%r, %r)" % (request.path, args, kwargs),
        status=410)


checkout_view = get_checkout_view()


urlpatterns = [
    url(r'^set-language/$', csrf_exempt(set_language), name="set-language"),
    url(r'^i18n.js$', javascript_catalog_all, name='js-catalog'),
    url(r'^checkout/$', checkout_view, name='checkout'),
    url(r'^checkout/(?P<phase>.+)/$', checkout_view, name='checkout'),
    url(r'^basket/$', csrf_exempt(BasketView.as_view()), name='basket'),
    url(r'^dashboard/$', login_required(DashboardView.as_view()), name="dashboard"),
    url(r'^toggle-allseeing/$', login_required(toggle_all_seeing), name="toggle-all-seeing"),
    url(r'^order/payment/(?P<pk>.+?)/(?P<key>.+?)/$',
        csrf_exempt(ProcessPaymentView.as_view()),
        kwargs={"mode": "payment"},
        name='order_process_payment'),
    url(r'^order/process-payment/(?P<pk>.+?)/(?P<key>.+?)/$',
        csrf_exempt(ProcessPaymentView.as_view()),
        kwargs={"mode": "return"},
        name='order_process_payment_return'),
    url(r'^order/payment-canceled/(?P<pk>.+?)/(?P<key>.+?)/$',
        ProcessPaymentView.as_view(),
        kwargs={"mode": "cancel"},
        name='order_payment_canceled'),
    url(r'^order/complete/(?P<pk>.+?)/(?P<key>.+?)/$',
        csrf_exempt(OrderCompleteView.as_view()),
        name='order_complete'),
    url(r'^order/verification/(?P<pk>.+?)/(?P<key>.+?)/$',
        _not_here_yet,
        name='order_requires_verification'),
    url(r'^order/get-attachment/(?P<order_pk>\d+)/(?P<key>.+?)/(?P<att_pk>\d+)/',
        _not_here_yet,
        name='secure_attachment'),
    url(r'^p/(?P<pk>\d+)-(?P<slug>.*)/$',
        csrf_exempt(ProductDetailView.as_view()),
        name='product'),
    url(r'^c/(?P<pk>\d+)-(?P<slug>.*)/$',
        csrf_exempt(CategoryView.as_view()),
        name='category'),
]

# TODO: Document `front_urls_pre`, `front_urls` and `front_urls_post`.


def _get_extension_urlpatterns(provide_category):
    return chain(*get_provide_objects(provide_category))

urlpatterns = list(chain(*(
    _get_extension_urlpatterns("front_urls_pre"),
    urlpatterns,
    _get_extension_urlpatterns("front_urls"),
    [url(r'^$', IndexView.as_view(), name='index')],
    _get_extension_urlpatterns("front_urls_post"),
)))
