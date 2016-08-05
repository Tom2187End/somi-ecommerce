# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from decimal import Decimal

from django.db import models
from django.db.transaction import atomic
from django.utils.crypto import get_random_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField

from shuup.core.fields import (
    InternalIdentifierField, MeasurementField, QuantityField
)
from shuup.core.signals import shipment_deleted

__all__ = ("Shipment", "ShipmentProduct")

CUBIC_MM_TO_CUBIC_METERS_DIVISOR = Decimal("1000000000")
GRAMS_TO_KILOGRAMS_DIVISOR = 1000


class ShipmentStatus(Enum):
    NOT_SENT = 0
    SENT = 1
    RECEIVED = 2  # if the customer deigns to tell us
    ERROR = 10
    DELETED = 20

    class Labels:
        NOT_SENT = _("not sent")
        SENT = _("sent")
        RECEIVED = _("received")
        ERROR = _("error")
        DELETED = _("deleted")


class ShipmentManager(models.Manager):

    def all_except_deleted(self):
        return self.exclude(status=ShipmentStatus.DELETED)


class Shipment(models.Model):
    order = models.ForeignKey("Order", related_name='shipments', on_delete=models.PROTECT, verbose_name=_("order"))
    supplier = models.ForeignKey(
        "Supplier", related_name='shipments', on_delete=models.PROTECT, verbose_name=_("supplier"))
    created_on = models.DateTimeField(auto_now_add=True, verbose_name=_("created on"))
    status = EnumIntegerField(ShipmentStatus, default=ShipmentStatus.NOT_SENT, verbose_name=_("status"))
    tracking_code = models.CharField(max_length=64, blank=True, verbose_name=_("tracking code"))
    description = models.CharField(max_length=255, blank=True, verbose_name=_("description"))
    volume = MeasurementField(unit="m3", verbose_name=_("volume"))
    weight = MeasurementField(unit="kg", verbose_name=_("weight"))
    identifier = InternalIdentifierField(unique=True)
    # TODO: documents = models.ManyToManyField(FilerFile)

    objects = ShipmentManager()

    class Meta:
        verbose_name = _('shipment')
        verbose_name_plural = _('shipments')

    def __init__(self, *args, **kwargs):
        super(Shipment, self).__init__(*args, **kwargs)
        if not self.identifier:
            if self.order and self.order.pk:
                prefix = '%s/%s/' % (self.order.pk, self.order.shipments.count())
            else:
                prefix = ''
            self.identifier = prefix + get_random_string(32)

    def __repr__(self):  # pragma: no cover
        return "<Shipment %s for order %s (tracking %r, created %s)>" % (
            self.pk, self.order_id, self.tracking_code, self.created_on
        )

    def save(self, *args, **kwargs):
        super(Shipment, self).save(*args, **kwargs)
        for product_id in self.products.values_list("product_id", flat=True):
            self.supplier.module.update_stock(product_id=product_id)

    def delete(self, using=None):
        raise NotImplementedError("Not implemented: Use `soft_delete()` for shipments.")

    @atomic
    def soft_delete(self, user=None):
        if self.status == ShipmentStatus.DELETED:
            return
        self.status = ShipmentStatus.DELETED
        self.save(update_fields=["status"])
        for product_id in self.products.values_list("product_id", flat=True):
            self.supplier.module.update_stock(product_id=product_id)
        self.order.update_shipping_status()
        shipment_deleted.send(sender=type(self), shipment=self)

    def is_deleted(self):
        return bool(self.status == ShipmentStatus.DELETED)

    def cache_values(self):
        """
        (Re)cache `.volume` and `.weight` for this Shipment from the ShipmentProducts within.
        """
        total_volume = 0
        total_weight = 0
        for quantity, volume, weight in self.products.values_list("quantity", "unit_volume", "unit_weight"):
            total_volume += quantity * volume
            total_weight += quantity * weight
        self.volume = total_volume
        self.weight = total_weight / GRAMS_TO_KILOGRAMS_DIVISOR

    @property
    def total_products(self):
        return (self.products.aggregate(quantity=models.Sum("quantity"))["quantity"] or 0)


@python_2_unicode_compatible
class ShipmentProduct(models.Model):
    shipment = models.ForeignKey(
        Shipment, related_name='products', on_delete=models.PROTECT, verbose_name=_("shipment")
    )
    product = models.ForeignKey(
        "Product", related_name='shipments', on_delete=models.CASCADE, verbose_name=_("product")
    )
    quantity = QuantityField(verbose_name=_("quantity"))

    # volume is m^3, not mm^3, because mm^3 are tiny. like ants.
    unit_volume = MeasurementField(unit="m3", verbose_name=_("unit volume"))
    unit_weight = MeasurementField(unit="g", verbose_name=_("unit weight"))

    class Meta:
        verbose_name = _('sent product')
        verbose_name_plural = _('sent products')

    def __str__(self):  # pragma: no cover
        return "%(quantity)s of '%(product)s' in Shipment #%(shipment_pk)s" % {
            'product': self.product,
            'quantity': self.quantity,
            'shipment_pk': self.shipment_id,
        }

    def cache_values(self):
        prod = self.product
        self.unit_volume = (prod.width * prod.height * prod.depth) / CUBIC_MM_TO_CUBIC_METERS_DIVISOR
        self.unit_weight = prod.gross_weight
