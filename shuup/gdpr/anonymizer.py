# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.utils.crypto import get_random_string

from shuup.core.models import CompanyContact, Contact, Order, PersonContact
from shuup.core.models._addresses import Address


class Anonymizer(object):
    mapping = {
        "phone": "null_phone",
        "ip_address": "null_ip",
        "first_name": "null_name",
        "last_name": "null_name",
        "name": "null_name",
        "postal_code": "null_zip",
        "zip_code": "null_zip",
        "www": "blank_value",
        "prefix": "blank_value",
        "suffix": "blank_value",
        "name_ext": "blank_value",
        "merchant_notes": "blank_value",
        "street": "random_string",
        "street1": "random_string",
        "street2": "random_string",
        "street3": "random_string",
        "street_address": "random_string",
        "tax_number": "random_number",
        "city": "random_string",
        "longitude": "none_value",
        "latitude": "none_value",
        "birth_date": "none_value",
        "data": "none_value",
        "email": "null_email",
        "username": "random_username"
    }

    anonymizers = {
        "PersonContact": "anonymize_contact",
        "CompanyContact": "anonymize_company",
        "User": "anonymize_user"
    }

    def anonymize(self, pk, cls):
        cls_name = cls.__name__
        if cls_name not in self.anonymizers:
            raise ValueError("Cannot anonymize %s" % cls_name)
        return getattr(self, self.anonymizers[cls_name])(pk)

    def random_string(self, len=8):
        return get_random_string(len)

    def none_value(self):
        return None

    def blank_value(self):
        return ""

    def null_zip(self):
        return get_random_string(6)

    def null_ip(self):
        return "0.0.0.0"

    def null_email(self):
        return "%s@%s.com" % (get_random_string(10), get_random_string(8))

    def null_name(self):
        return get_random_string(8)

    def null_phone(self):
        return get_random_string(9, "1234567890")

    def random_number(self):
        return int(get_random_string(9, "123456789"))

    def random_username(self):
        return get_random_string(32, "1234567890")

    def anonymize_contact(self, pk):
        contact = Contact.objects.get(pk=pk)

        # make sure to remove from marketing before we lost the contact email
        contact.marketing_permission = False
        contact.save()

        # anonymize all saved addresses
        for saved_address in contact.savedaddress_set.all():
            self.anonymize_object(saved_address.address)

        # anonymize all orders
        for order in contact.customer_orders.all():
            self.anonymize_order(order)

        for order in contact.orderer_orders.all():
            self.anonymize_order(order)

        # anonymize all Front baskets
        for basket in contact.customer_baskets.all():
            self.anonymize_object(basket)
        for basket in contact.orderer_baskets.all():
            self.anonymize_object(basket)

        # anonymize all Core baskets
        for basket in contact.customer_core_baskets.all():
            self.anonymize_object(basket)
        for basket in contact.orderer_core_baskets.all():
            self.anonymize_object(basket)

        self.anonymize_object(contact.default_shipping_address)
        self.anonymize_object(contact.default_billing_address)
        self.anonymize_object(contact)

        contact.is_active = False
        contact.save()

    def anonymize_company(self, company):
        assert isinstance(company, CompanyContact)
        self.anonymize_contact(company.id)

    def anonymize_person(self, person):
        assert isinstance(person, PersonContact)
        self.anonymize_contact(person.pk)

    def anonymize_order(self, order):
        assert isinstance(order, Order)
        self.anonymize_object(order)

        self.anonymize_object(order.shipping_address, save=False)
        self.anonymize_object(order.billing_address, save=False)

        # bypass Protected model save() invoking super directly
        Address.save(order.shipping_address)
        Address.save(order.billing_address)

    def anonymize_object(self, obj, save=True):
        if not obj:
            return

        for field, attr in six.iteritems(self.mapping):
            if not hasattr(obj, field):
                continue
            val = getattr(self, attr)()

            try:
                setattr(obj, field, val)
            except AttributeError:
                pass

        if save:
            obj.save()

    def anonymize_queryset(self, qs):
        for qs_obj in qs:
            self.anonymize_object(qs_obj)

    def anonymize_user(self, user):
        self.anonymize_object(user)
        user.is_active = False
        user.save()
