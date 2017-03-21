# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, UpdateView

from shuup.admin.toolbar import PostActionButton, Toolbar
from shuup.admin.utils.forms import add_form_errors_as_messages
from shuup.admin.utils.urls import get_model_url
from shuup.core.excs import NoPaymentToCreateException
from shuup.core.models import Order, PaymentStatus
from shuup.utils.money import Money


class OrderCreatePaymentView(UpdateView):
    model = Order
    template_name = "shuup/admin/orders/create_payment.jinja"
    context_object_name = "order"
    form_class = forms.Form  # Augmented manually

    def get_context_data(self, **kwargs):
        context = super(OrderCreatePaymentView, self).get_context_data(**kwargs)
        context["title"] = _("Create Payment -- %s") % context["order"]
        context["toolbar"] = Toolbar([
            PostActionButton(
                icon="fa fa-check-circle",
                form_id="create_payment",
                text=_("Create Payment"),
                extra_css_class="btn-success",
            ),
        ])
        return context

    def get_form_kwargs(self):
        kwargs = super(OrderCreatePaymentView, self).get_form_kwargs()
        kwargs.pop("instance")
        return kwargs

    def get_form(self, form_class):
        form = super(OrderCreatePaymentView, self).get_form(form_class)
        order = self.object
        form.fields["amount"] = forms.DecimalField(
            required=True,
            min_value=0,
            max_value=order.get_total_unpaid_amount().value,
            initial=0,
            label=_("Payment amount"),
        )
        return form

    def form_invalid(self, form):
        add_form_errors_as_messages(self.request, form)
        return super(OrderCreatePaymentView, self).form_invalid(form)

    def form_valid(self, form):
        order = self.object
        amount = Money(form.cleaned_data["amount"], order.currency)
        if amount.value == 0:
            messages.error(self.request, _("Payment amount cannot be 0"))
            return self.form_invalid(form)
        try:
            payment = order.create_payment(amount, description="Manual payment")
            messages.success(self.request, _("Payment %s created.") % payment.payment_identifier)
        except NoPaymentToCreateException:
            messages.error(self.request, _("Order has already been paid"))
            return self.form_invalid(form)
        else:
            return HttpResponseRedirect(get_model_url(order))


class OrderSetPaidView(DetailView):
    model = Order

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(get_model_url(self.get_object()))

    def post(self, request, *args, **kwargs):
        order = self.object = self.get_object()
        error = False
        if order.payment_status not in (PaymentStatus.DEFERRED, PaymentStatus.NOT_PAID):
            error = True
            messages.error(self.request, _("Only orders which are not paid or deferred can be set as paid."))
        if order.taxful_total_price:
            error = True
            messages.error(self.request, _("Only zero price orders can be set as paid without creating a payment."))
        if not error:
            amount = Money(0, order.shop.currency)
            order.create_payment(amount, description=_("Zero amount payment"))
            messages.success(self.request, _("Order marked as paid."))
        return HttpResponseRedirect(get_model_url(self.get_object()))
