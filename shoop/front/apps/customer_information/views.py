# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shoop.core.models import get_company_contact, get_person_contact
from shoop.utils.form_group import FormGroup

from .forms import AddressForm, CompanyContactForm, PersonContactForm


class CustomerEditView(FormView):
    template_name = "shoop/customer_information/edit_customer.jinja"

    def get_form(self, form_class):
        contact = get_person_contact(self.request.user)
        form_group = FormGroup(**self.get_form_kwargs())
        form_group.add_form_def("billing", AddressForm, kwargs={"instance": contact.default_billing_address})
        form_group.add_form_def("shipping", AddressForm, kwargs={"instance": contact.default_shipping_address})
        form_group.add_form_def("contact", PersonContactForm, kwargs={"instance": contact})
        return form_group

    def form_valid(self, form):
        contact = form["contact"].save()
        user = contact.user
        billing_address = form["billing"].save()
        shipping_address = form["shipping"].save()
        if billing_address.pk != contact.default_billing_address_id:  # Identity changed due to immutability
            contact.default_billing_address = billing_address
        if shipping_address.pk != contact.default_shipping_address_id:  # Identity changed due to immutability
            contact.default_shipping_address = shipping_address

        if not bool(get_company_contact(self.request.user)):  # Only update user details for non-company members
            user.email = contact.email
            user.first_name = contact.first_name
            user.last_name = contact.last_name
            user.save()

        contact.save()
        messages.success(self.request, _("Account information saved successfully."))
        return redirect("shoop:customer_edit")


class CompanyEditView(FormView):
    template_name = "shoop/customer_information/edit_company.jinja"

    def get_form(self, form_class):
        contact = get_company_contact(self.request.user)
        form_group = FormGroup(**self.get_form_kwargs())
        form_group.add_form_def(
            "billing", AddressForm, kwargs={"instance": contact.default_billing_address if contact else None}
        )
        form_group.add_form_def(
            "shipping", AddressForm, kwargs={"instance": contact.default_shipping_address if contact else None}
        )
        form_group.add_form_def("contact", CompanyContactForm, kwargs={"instance": contact})
        return form_group

    def form_valid(self, form):
        company = form["contact"].save()
        user = self.request.user
        person = get_person_contact(user)
        company.members.add(person)
        billing_address = form["billing"].save()
        shipping_address = form["shipping"].save()
        if billing_address.pk != company.default_billing_address_id:  # Identity changed due to immutability
            company.default_billing_address = billing_address
        if shipping_address.pk != company.default_shipping_address_id:  # Identity changed due to immutability
            company.default_shipping_address = shipping_address

        user.email = company.email
        user.first_name = company.name
        user.last_name = ""
        user.save()

        company.save()
        messages.success(self.request, _("Company information saved successfully."))
        return redirect("shoop:company_edit")
