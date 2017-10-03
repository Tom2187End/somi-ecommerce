# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import warnings

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from shuup.admin.toolbar import (
    DropdownActionButton, PostActionButton, Toolbar, URLActionButton
)
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.apps.provides import get_provide_objects
from shuup.core.models import CompanyContact, Contact
from shuup.front.apps.registration.signals import company_contact_activated
from shuup.utils.deprecation import RemovedFromShuupWarning
from shuup.utils.excs import Problem


class ContactDetailToolbar(Toolbar):
    def __init__(self, contact, request):
        self.contact = contact
        self.request = request
        self.user = getattr(self.contact, "user", None)
        super(ContactDetailToolbar, self).__init__()
        self.build()

    def build_renew_password_button(self):
        disable_reason = None

        if "shuup.front.apps.auth" not in settings.INSTALLED_APPS:
            disable_reason = _("The Shuup frontend is not enabled.")
        elif not self.user:
            disable_reason = _("Contact has no associated user.")
        elif not getattr(self.user, "email", None):
            disable_reason = _("User has no associated email.")

        self.append(PostActionButton(
            post_url=reverse("shuup_admin:contact.reset_password", kwargs={"pk": self.contact.pk}),
            name="pk",
            value=self.contact.pk,
            text=_(u"Reset password"),
            tooltip=_(u"Send a password renewal email."),
            confirm=_("Are you sure you wish to send a password recovery email to %s?") % self.contact.email,
            icon="fa fa-undo",
            disable_reason=disable_reason,
            extra_css_class="btn-gray btn-inverse",
        ))

    def build_new_user_button(self):
        if self.user or isinstance(self.contact, CompanyContact):
            return
        self.append(URLActionButton(
            url=reverse("shuup_admin:user.new") + "?contact_id=%s" % self.contact.pk,
            text=_(u"New User"),
            tooltip=_(u"Create a user for the contact."),
            icon="fa fa-star",
            extra_css_class="btn-gray btn-inverse",
            required_permissions=get_default_model_permissions(get_user_model()),
        ))

    def build_new_order_button(self):
        self.append(URLActionButton(
            url=reverse("shuup_admin:order.new") + "?contact_id=%s" % self.contact.pk,
            text=_(u"New Order"),
            tooltip=_(u"Create an order for the contact."),
            icon="fa fa-plus",
            extra_css_class="btn-success",
            required_permissions=["shuup.add_order"],
        ))

    def build_deactivate_button(self):
        self.append(PostActionButton(
            post_url=self.request.path,
            name="set_is_active",
            value="0" if self.contact.is_active else "1",
            icon="fa fa-times-circle",
            text=_(u"Deactivate Contact") if self.contact.is_active else _(u"Activate Contact"),
            extra_css_class="btn-gray",
        ))

    def build_provides_buttons(self):
        action_menu_items = []
        for button in get_provide_objects("admin_contact_toolbar_action_item"):
            if button.visible_for_object(self.contact):
                action_menu_items.append(button(object=self.contact))

        if action_menu_items:
            self.append(
                DropdownActionButton(
                    action_menu_items,
                    icon="fa fa-star",
                    text=_(u"Actions"),
                    extra_css_class="btn-info",
                )
            )

        for button in get_provide_objects("admin_contact_toolbar_button"):
            warnings.warn(
                "admin_contact_toolbar_button provider is deprecated, use admin_contact_toolbar_action_item instead",
                RemovedFromShuupWarning)
            self.append(button(self.contact))

    def build(self):
        self.append(URLActionButton(
            url=reverse("shuup_admin:contact.edit", kwargs={"pk": self.contact.pk}),
            icon="fa fa-pencil",
            text=_(u"Edit..."),
            extra_css_class="btn-info",
        ))
        self.build_renew_password_button()
        self.build_new_user_button()
        self.build_deactivate_button()
        self.build_new_order_button()
        self.build_provides_buttons()


class ContactDetailView(DetailView):
    model = Contact
    template_name = "shuup/admin/contacts/detail.jinja"
    context_object_name = "contact"

    def get_object(self, *args, **kwargs):
        obj = super(ContactDetailView, self).get_object(*args, **kwargs)

        if settings.SHUUP_MANAGE_CONTACTS_PER_SHOP and not self.request.user.is_superuser:
            shop = self.request.shop
            if shop not in obj.shops.all():
                raise PermissionDenied()

        return obj

    def get_context_data(self, **kwargs):
        context = super(ContactDetailView, self).get_context_data(**kwargs)
        context["toolbar"] = ContactDetailToolbar(contact=self.object, request=self.request)
        context["title"] = "%s: %s" % (
            self.object._meta.verbose_name.title(),
            force_text(self.object)
        )
        context["contact_sections"] = []

        contact_sections_provides = sorted(get_provide_objects("admin_contact_section"), key=lambda x: x.order)
        for admin_contact_section in contact_sections_provides:
            # Check whether the ContactSection should be visible for the current object
            if admin_contact_section.visible_for_object(self.object, self.request):
                context["contact_sections"].append(admin_contact_section)
                # add additional context data where the key is the contact_section identifier
                section_context = admin_contact_section.get_context_data(self.object, self.request)
                context[admin_contact_section.identifier] = section_context

        return context

    def _handle_set_is_active(self):
        old_state = self.object.is_active
        state = bool(int(self.request.POST["set_is_active"]))
        if not state and hasattr(self.object, "user"):
            if (getattr(self.object.user, 'is_superuser', False) and
                    not getattr(self.request.user, 'is_superuser', False)):
                raise Problem(_("You can not deactivate a superuser."))
            if self.object.user == self.request.user:
                raise Problem(_("You can not deactivate yourself."))

        self.object.is_active = state
        self.object.save(update_fields=("is_active",))
        messages.success(self.request, _("%(contact)s is now %(state)s.") % {
            "contact": self.object,
            "state": _("active") if state else _("inactive")
        })

        if (self.object.is_active and self.object.is_active != old_state
                and isinstance(self.object, CompanyContact)):
            company_contact_activated.send(sender=type(self.object),
                                           instance=self.object,
                                           request=self.request)

        return HttpResponseRedirect(self.request.path)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "set_is_active" in request.POST:
            return self._handle_set_is_active()
        return super(ContactDetailView, self).post(request, *args, **kwargs)
