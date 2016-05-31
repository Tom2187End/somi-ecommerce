# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.views.generic import DetailView

from shoop.admin.toolbar import PostActionButton, Toolbar, URLActionButton
from shoop.admin.utils.urls import get_model_url
from shoop.apps.provides import get_provide_objects
from shoop.core.models import Order, OrderStatus, OrderStatusRole
from shoop.utils.excs import Problem


class OrderDetailView(DetailView):
    model = Order
    template_name = "shoop/admin/orders/detail.jinja"
    context_object_name = "order"

    def get_toolbar(self):
        order = self.object
        if order.is_canceled():
            return
        toolbar = Toolbar()
        toolbar.append(URLActionButton(
            text=_("Create Payment"),
            icon="fa fa-money",
            disable_reason=_("This order cannot be paid at this point") if order.is_paid() else None,
            url=reverse("shoop_admin:order.create-payment", kwargs={"pk": order.pk}),
            extra_css_class="btn-info"
        ))

        toolbar.append(URLActionButton(
            text=_("Create Shipment"),
            icon="fa fa-truck",
            disable_reason=_("There are no products to ship") if not order.get_unshipped_products() else None,
            url=reverse("shoop_admin:order.create-shipment", kwargs={"pk": order.pk}),
            extra_css_class="btn-info"
        ))

        toolbar.append(PostActionButton(
            post_url=reverse("shoop_admin:order.set-status", kwargs={"pk": order.pk}),
            name="status",
            value=OrderStatus.objects.get_default_complete().pk,
            text=_("Set Complete"),
            icon="fa fa-check-circle",
            disable_reason=(
                _("This order can not be set as complete at this point")
                if not order.can_set_complete()
                else None
            ),
            extra_css_class="btn-success"
        ))

        toolbar.append(PostActionButton(
            post_url=reverse("shoop_admin:order.set-status", kwargs={"pk": order.pk}),
            name="status",
            value=OrderStatus.objects.get_default_canceled().pk,
            text=_("Cancel Order"),
            icon="fa fa-trash",
            disable_reason=(
                _("Paid, shipped, or canceled orders cannot be canceled")
                if not order.can_set_canceled()
                else None
            ),
            extra_css_class="btn-danger btn-inverse"
        ))
        toolbar.append(URLActionButton(
            text=_("Edit order"),
            icon="fa fa-money",
            disable_reason=_("This order cannot modified at this point") if not order.can_edit() else None,
            url=reverse("shoop_admin:order.edit", kwargs={"pk": order.pk}),
            extra_css_class="btn-info"
        ))

        for button in get_provide_objects("admin_order_toolbar_button"):
            toolbar.append(button(order))

        return toolbar

    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        context["toolbar"] = self.get_toolbar()
        context["title"] = force_text(self.object)
        context["order_sections"] = []

        order_sections_provides = sorted(get_provide_objects("admin_order_section"), key=lambda x: x.order)
        for admin_order_section in order_sections_provides:
            # Check whether the OrderSection should be visible for the current object
            if admin_order_section.visible_for_order(self.object):
                context["order_sections"].append(admin_order_section)
                # add additional context data where the key is the order_section identifier
                context[admin_order_section.identifier] = admin_order_section.get_context_data(self.object)

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
        message = _("Order status changed: %s to %s") % (old_status, new_status)
        order.add_log_entry(message, user=request.user, identifier="status_change")
        messages.success(self.request, message)

        return HttpResponseRedirect(get_model_url(self.get_object()))
