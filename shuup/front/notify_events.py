# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import PaymentStatus, ShipmentStatus, ShippingStatus
from shuup.core.order_creator.signals import order_creator_finished
from shuup.core.signals import (
    payment_created, refund_created, shipment_created, shipment_deleted
)
from shuup.notify.base import Event, Variable
from shuup.notify.typology import Email, Enum, Language, Model, Phone


class OrderReceived(Event):
    identifier = "order_received"
    name = _("Order Received")

    order = Variable(_("Order"), type=Model("shuup.Order"))
    customer_email = Variable(_("Customer Email"), type=Email)
    customer_phone = Variable(_("Customer Phone"), type=Phone)
    language = Variable(_("Language"), type=Language)


class ShipmentCreated(Event):
    identifier = "shipment_created"
    name = _("Shipment Created")

    order = Variable(_("Order"), type=Model("shuup.Order"))
    customer_email = Variable(_("Customer Email"), type=Email)
    customer_phone = Variable(_("Customer Phone"), type=Phone)
    language = Variable(_("Language"), type=Language)

    shipment = Variable(_("Shipment"), type=Model("shuup.Shipment"))
    shipping_status = Variable(_("Order Shipping Status"), type=Enum(ShippingStatus))
    shipment_status = Variable(_("Shipment Status"), type=Enum(ShipmentStatus))


class ShipmentDeleted(Event):
    identifier = "shipment_deleted"
    name = _("Shipment Deleted")

    order = Variable(_("Order"), type=Model("shuup.Order"))
    customer_email = Variable(_("Customer Email"), type=Email)
    customer_phone = Variable(_("Customer Phone"), type=Phone)
    language = Variable(_("Language"), type=Language)

    shipment = Variable(_("Shipment"), type=Model("shuup.Shipment"))
    shipping_status = Variable(_("Order Shipping Status"), type=Enum(ShippingStatus))


class PaymentCreated(Event):
    identifier = "payment_created"
    name = _("Payment Created")

    order = Variable(_("Order"), type=Model("shuup.Order"))
    customer_email = Variable(_("Customer Email"), type=Email)
    customer_phone = Variable(_("Customer Phone"), type=Phone)
    language = Variable(_("Language"), type=Language)

    payment_status = Variable(_("Order Payment Status"), type=Enum(PaymentStatus))
    payment = Variable(_("Payment"), type=Model("shuup.Payment"))


class RefundCreated(Event):
    identifier = "refund_created"
    name = _("Refund Created")

    order = Variable(_("Order"), type=Model("shuup.Order"))
    customer_email = Variable(_("Customer Email"), type=Email)
    customer_phone = Variable(_("Customer Phone"), type=Phone)
    language = Variable(_("Language"), type=Language)

    payment_status = Variable(_("Order Payment Status"), type=Enum(PaymentStatus))


@receiver(order_creator_finished)
def send_order_received_notification(order, **kwargs):
    OrderReceived(
        order=order,
        customer_email=order.email,
        customer_phone=order.phone,
        language=order.language
    ).run()


@receiver(shipment_created)
def send_shipment_created_notification(order, shipment, **kwargs):
    ShipmentCreated(
        order=order,
        customer_email=order.email,
        customer_phone=order.phone,
        language=order.language,
        shipment=shipment,
        shipping_status=order.shipping_status,
        shipment_status=shipment.status
    ).run()


@receiver(shipment_deleted)
def send_shipment_deleted_notification(shipment, **kwargs):
    ShipmentDeleted(
        order=shipment.order,
        customer_email=shipment.order.email,
        customer_phone=shipment.order.phone,
        language=shipment.order.language,
        shipment=shipment,
        shipping_status=shipment.order.shipping_status
    ).run()


@receiver(payment_created)
def send_payment_created_notification(order, payment, **kwargs):
    PaymentCreated(
        order=order,
        customer_email=order.email,
        customer_phone=order.phone,
        language=order.language,
        payment_status=order.payment_status,
        payment=payment
    ).run()


@receiver(refund_created)
def send_refund_created_notification(order, refund_lines, **kwargs):
    RefundCreated(
        order=order,
        customer_email=order.email,
        customer_phone=order.phone,
        language=order.language,
        payment_status=order.payment_status
    ).run()
