# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib import messages
from django.db.transaction import atomic
from django.forms.formsets import (
    BaseFormSet, DELETION_FIELD_NAME, formset_factory
)
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.admin.forms.widgets import ContactChoiceWidget
from shuup.core.models import Contact, ContactGroup
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class ContactGroupBaseForm(MultiLanguageModelForm):
    class Meta:
        model = ContactGroup
        fields = ("name",)

    def __init__(self, *args, **kwargs):
        super(ContactGroupBaseForm, self).__init__(*args, **kwargs)
        self.fields['price_display_mode'] = forms.ChoiceField(
            choices=_PRICE_DISPLAY_MODE_CHOICES,
            label=_("Price display mode"),
            initial=_get_price_display_mode(self.instance),
            help_text=_("Set how prices are displayed to contacts in this group."))

    def save(self, commit=True):
        price_display_mode = self.cleaned_data['price_display_mode']
        _set_price_display_mode(self.instance, price_display_mode)
        super(ContactGroupBaseForm, self).save(commit=commit)


_PRICE_DISPLAY_MODE_CHOICES = [
    ('none', _("unspecified")),
    ('with_taxes', _("show prices with taxes included")),
    ('without_taxes', _("show pre-tax prices")),
    ('hide', _("hide prices")),
]


def _get_price_display_mode(contact_group):
    taxes = contact_group.show_prices_including_taxes
    hide = contact_group.hide_prices
    if hide is None and taxes is None:
        return 'none'
    elif hide:
        return 'hide'
    elif taxes:
        return 'with_taxes'
    else:
        return 'without_taxes'


def _set_price_display_mode(contact_group, price_display_mode):
    if price_display_mode == 'none':
        contact_group.show_prices_including_taxes = None
        contact_group.hide_prices = None
    elif price_display_mode == 'hide':
        contact_group.show_prices_including_taxes = None
        contact_group.hide_prices = True
    elif price_display_mode == 'with_taxes':
        contact_group.show_prices_including_taxes = True
        contact_group.hide_prices = None
    elif price_display_mode == 'without_taxes':
        contact_group.show_prices_including_taxes = False
        contact_group.hide_prices = None


class ContactGroupBaseFormPart(FormPart):
    priority = 0

    def get_form_defs(self):
        contact_group = self.object

        yield TemplatedFormDef(
            "base",
            ContactGroupBaseForm,
            template_name="shuup/admin/contact_groups/_edit_base_contact_group_form.jinja",
            required=True,
            kwargs={"instance": contact_group, "languages": settings.LANGUAGES}
        )

    def form_valid(self, form):
        self.object = form["base"].save()


class ContactGroupMembersForm(forms.Form):
    member = forms.ModelChoiceField(
        queryset=Contact.objects.all(),
        widget=ContactChoiceWidget(empty_text=""),
        label=_('member')
    )


class ContactGroupMembersFormSet(BaseFormSet):
    def __init__(self, **kwargs):
        kwargs.pop("empty_permitted", None)
        self.request = kwargs.pop("request", None)
        self.contact_group = kwargs.pop("contact_group")
        super(ContactGroupMembersFormSet, self).__init__(**kwargs)

    def _construct_form(self, i, **kwargs):
        form = super(ContactGroupMembersFormSet, self)._construct_form(i, **kwargs)
        form.fields[DELETION_FIELD_NAME].label = _("Remove")
        return form

    def save(self):
        contact_group = self.contact_group
        current_members = set(contact_group.members.all())
        selected_members, removed_members = self.get_selected_and_removed()

        with atomic():
            members_to_add = selected_members - current_members
            members_to_remove = current_members & removed_members
            for member in members_to_remove:
                contact_group.members.remove(member)
            for member in members_to_add:
                contact_group.members.add(member)

        message_parts = []
        if members_to_add:
            add_count = len(members_to_add)
            message_parts.append(ungettext("%(count)s member added", "%(count)s members added",
                                 add_count) % {"count": add_count})
        if members_to_remove:
            remove_count = len(members_to_remove)
            message_parts.append(ungettext("%(count)s member removed", "%(count)s members removed",
                                 remove_count) % {"count": remove_count})
        if message_parts and self.request:
            messages.success(self.request, ", ".join(message_parts) + ".")

    def get_selected_and_removed(self):
        deleted_forms = self.deleted_forms
        removed_members = set()
        selected_members = set()
        for member_form in self.forms:
            member = member_form.cleaned_data.get("member")
            if not member:
                continue
            if member_form in deleted_forms:
                removed_members.add(member)
            else:
                selected_members.add(member)
        return (selected_members, removed_members)


class ContactGroupMembersFormPart(FormPart):
    priority = 1

    def get_form_defs(self):
        contact_group = self.object
        form = formset_factory(ContactGroupMembersForm, ContactGroupMembersFormSet, extra=1, can_delete=True)
        template_name = "shuup/admin/contact_groups/_edit_members_form.jinja"

        if contact_group.pk:
            yield TemplatedFormDef(
                "members",
                form,
                template_name=template_name,
                required=False,
                kwargs={"contact_group": contact_group, "request": self.request}
            )

    def form_valid(self, form):
        try:
            member_formset = form["members"]
        except KeyError:
            return
        member_formset.save()
