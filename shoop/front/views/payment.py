# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from __future__ import with_statement
from django.core.exceptions import ImproperlyConfigured

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView

from shoop.core.models import Order


def get_payment_urls(request, order):
    kwargs = dict(pk=order.pk, key=order.key)
    return {
        "payment": request.build_absolute_uri(reverse("shoop:order_process_payment", kwargs=kwargs)),
        "return": request.build_absolute_uri(reverse("shoop:order_process_payment_return", kwargs=kwargs)),
        "cancel": request.build_absolute_uri(reverse("shoop:order_payment_canceled", kwargs=kwargs))
    }


class ProcessPaymentView(DetailView):
    model = Order
    context_object_name = "order"

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, pk=self.kwargs["pk"], key=self.kwargs["key"])

    def get_context_data(self, **kwargs):
        context = super(ProcessPaymentView, self).get_context_data(**kwargs)
        context["payment_urls"] = get_payment_urls(self.request, self.object)
        return context

    def dispatch(self, request, *args, **kwargs):
        mode = self.kwargs["mode"]
        order = self.object = self.get_object()
        payment_method = (order.payment_method if order.payment_method_id else None)
        if mode == "payment":
            if not order.is_paid():
                if payment_method:
                    return payment_method.get_payment_process_response(
                        order=order, urls=get_payment_urls(request, order))
        elif mode == "return":
            if payment_method:
                payment_method.process_payment_return_request(order=order, request=request)
        elif mode == "cancel":
            self.template_name = "shoop/front/order/payment_canceled.jinja"
            return self.render_to_response(self.get_context_data(object=order))
        else:
            raise ImproperlyConfigured("Unknown ProcessPaymentView mode: %s" % mode)

        return redirect("shoop:order_complete", pk=order.pk, key=order.key)
