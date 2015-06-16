# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.management.base import BaseCommand
from django.db.models import Model
from django.db.transaction import atomic
from shoop.core.defaults.order_statuses import create_default_order_statuses
from shoop.core.models import (
    Category, OrderStatus, PaymentMethod, ProductType,
    SalesUnit, ShippingMethod, Shop, Supplier, TaxClass,
    ShopStatus
)
from six import print_


def schema(model, identifier, **info):
    return locals()


class Initializer(object):
    schemata = [
        schema(Shop, "default", name="Default Shop", status=ShopStatus.ENABLED),
        schema(ProductType, "default", name="Standard Product"),
        schema(ProductType, "download", name="Download Product"),
        schema(TaxClass, "default", name="Default Tax Class"),
        schema(PaymentMethod, "default", name="Default Payment Method", tax_class=TaxClass),
        schema(ShippingMethod, "default", name="Default Shipping Method", tax_class=TaxClass),
        schema(Supplier, "default", name="Default Supplier"),
        schema(SalesUnit, "pcs", name="Pieces"),
        schema(Category, "default", name="Default Category"),
    ]

    def __init__(self):
        self.objects = {}

    def process_schema(self, schema):
        model = schema["model"]
        assert issubclass(model, Model)
        identifier_attr = getattr(model, "identifier_attr", "identifier")
        obj = model.objects.filter(**{identifier_attr: schema["identifier"]}).first()
        if obj:
            return obj
        print_("Creating %s..." % model._meta.verbose_name, end=" ")
        obj = model()
        setattr(obj, identifier_attr, schema["identifier"])
        for key, value in schema["info"].items():
            if value in self.objects:
                value = self.objects[value]
            setattr(obj, key, value)
        obj.full_clean()
        obj.save()
        print_(obj)
        return obj

    def run(self):
        for schema in self.schemata:
            self.objects[schema["model"]] = self.process_schema(schema)
        if not OrderStatus.objects.exists():
            print_("Creating order statuses...", end=" ")
            create_default_order_statuses()
            print_("done.")
        print_("Initialization done.")


class Command(BaseCommand):
    leave_locale_alone = True

    def handle(self, *args, **options):
        with atomic():
            Initializer().run()
