# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.views.generic import DetailView

from shuup.admin.modules.orders.toolbar import OrderDetailToolbar
from shuup.admin.utils.urls import get_model_url
from shuup.apps.provides import get_provide_objects
from shuup.core.models import Order, OrderStatus, OrderStatusRole
from shuup.utils.excs import Problem


class OrderDetailView(DetailView):
    model = Order
    template_name = "shuup/admin/orders/detail.jinja"
    context_object_name = "order"

    def get_toolbar(self):
        return OrderDetailToolbar(self.object)

    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        context["toolbar"] = self.get_toolbar()
        context["title"] = force_text(self.object)
        context["order_sections"] = []

        provided_information = []
        for provided_info in sorted(get_provide_objects("admin_order_information"), key=lambda x: x.order):
            info = provided_info(self.object)
            if info.provides_info():
                provided_information.append((info.title, info.information))
        context["provided_information"] = provided_information

        order_sections_provides = sorted(get_provide_objects("admin_order_section"), key=lambda x: x.order)
        for admin_order_section in order_sections_provides:
            # Check whether the Section should be visible for the current object
            if admin_order_section.visible_for_object(self.object, self.request):
                context["order_sections"].append(admin_order_section)
                # add additional context data where the key is the order_section identifier
                section_context = admin_order_section.get_context_data(self.object, self.request)
                context[admin_order_section.identifier] = section_context

        return context


class OrderSetStatusView(DetailView):
    model = Order

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(get_model_url(self.get_object()))

    def post(self, request, *args, **kwargs):
        order = self.object = self.get_object()
        new_status = OrderStatus.objects.get(pk=int(request.POST["status"]))
        old_status = order.status
        if new_status.role == OrderStatusRole.COMPLETE and not order.can_set_complete():
            raise Problem(_("Unable to set order as completed at this point"))
        if new_status.role == OrderStatusRole.CANCELED and not order.can_set_canceled():
            raise Problem(_("Paid, shipped, or canceled orders cannot be canceled"))
        order.status = new_status
        order.save(update_fields=("status",))
        message = _("Order status changed: {old_status} to {new_status}").format(
            old_status=old_status, new_status=new_status)
        order.add_log_entry(message, user=request.user, identifier="status_change")
        messages.success(self.request, message)

        return HttpResponseRedirect(get_model_url(self.get_object()))
