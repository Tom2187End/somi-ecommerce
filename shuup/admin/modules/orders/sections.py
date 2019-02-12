# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from shuup.admin.base import Section
from shuup.apps.provides import get_provide_objects
from shuup.core.models import Shipment
from shuup.core.models._orders import OrderLogEntry


class BasicDetailsOrderSection(Section):
    identifier = "order_details"
    name = _("Details")
    icon = "fa-info-circle"
    template = "shuup/admin/orders/_detail_section.jinja"
    order = 0

    @classmethod
    def visible_for_object(cls, order, request=None):
        return True

    @classmethod
    def get_context_data(cls, order, request=None):
        provided_information = []
        for provided_info in sorted(get_provide_objects("admin_order_information"), key=lambda x: x.order):
            info = provided_info(order)
            if info.provides_info():
                provided_information.append((info.title, info.information))
        return {
            "provided_information": provided_information
        }


class PaymentOrderSection(Section):
    identifier = "payments"
    name = _("Payments")
    icon = "fa-dollar"
    template = "shuup/admin/orders/_detail_payments.jinja"
    extra_js = "shuup/admin/orders/_detail_payments_js.jinja"
    order = 1

    @classmethod
    def visible_for_object(cls, order, request=None):
        return order.payments.exists()

    @classmethod
    def get_context_data(cls, order, request=None):
        return order.payments.all()


class ShipmentSection(Section):
    identifier = "shipments"
    name = _("Shipments")
    icon = "fa-truck"
    template = "shuup/admin/orders/_order_shipments.jinja"
    order = 2

    @staticmethod
    def visible_for_object(order, request=None):
        return Shipment.objects.filter(order=order).exists()

    @staticmethod
    def get_context_data(order, request=None):
        return Shipment.objects.filter(order=order).order_by("-created_on").all()


class LogEntriesOrderSection(Section):
    identifier = "log_entries"
    name = _("Log Entries")
    icon = "fa-pencil"
    template = "shuup/admin/orders/_order_log_entries.jinja"
    extra_js = "shuup/admin/orders/_order_log_entries_extra_js.jinja"
    order = 3

    @classmethod
    def visible_for_object(cls, order, request=None):
        return True

    @classmethod
    def get_context_data(cls, order, request=None):
        return OrderLogEntry.objects.filter(target=order).order_by("-created_on").all()[:12]
        # TODO: We're currently trimming to 12 entries, probably need pagination


class AdminCommentSection(Section):
    identifier = "admin_comment"
    name = _("Admin comment/notes")
    icon = "fa-comment-o"
    template = "shuup/admin/orders/_admin_comment.jinja"
    extra_js = "shuup/admin/orders/_admin_comment_extra_js.jinja"
    order = 4

    @classmethod
    def visible_for_object(cls, order, request=None):
        return True

    @classmethod
    def get_context_data(cls, order, request=None):
        return None
