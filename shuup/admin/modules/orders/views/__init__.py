# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from .addresses import OrderAddressEditView
from .detail import OrderDetailView, OrderSetStatusView
from .edit import OrderEditView, UpdateAdminCommentView
from .list import OrderListView
from .log import NewLogEntryView
from .payment import OrderCreatePaymentView, OrderDeletePaymentView, OrderSetPaidView
from .refund import OrderCreateFullRefundView, OrderCreateRefundView
from .shipment import OrderCreateShipmentView, ShipmentDeleteView, ShipmentListView, ShipmentSetSentView
from .status import OrderDeleteStatusHistoryView, OrderStatusEditView, OrderStatusListView

__all__ = [
    "NewLogEntryView",
    "OrderAddressEditView",
    "OrderDetailView",
    "OrderEditView",
    "OrderListView",
    "OrderCreateFullRefundView",
    "OrderCreatePaymentView",
    "OrderCreateRefundView",
    "OrderCreateShipmentView",
    "OrderDeletePaymentView",
    "OrderDeleteStatusHistoryView",
    "OrderSetPaidView",
    "OrderSetStatusView",
    "OrderStatusEditView",
    "OrderStatusListView",
    "ShipmentDeleteView",
    "ShipmentListView",
    "ShipmentSetSentView",
    "UpdateAdminCommentView",
]
