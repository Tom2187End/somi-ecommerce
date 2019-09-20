# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import logging

from django import forms
from django.conf import settings
from django.core.mail.message import EmailMessage
from django.utils.translation import ugettext as _

from shuup.admin.forms.widgets import TextEditorWidget
from shuup.notify.base import Action, Binding
from shuup.notify.enums import ConstantUse, TemplateUse
from shuup.notify.typology import Email, Language, Text


class SendEmail(Action):
    EMAIL_CONTENT_TYPE_CHOICES = (
        ('plain', _('Plain text')),
        ('html', _('HTML'))
    )

    identifier = "send_email"
    template_use = TemplateUse.MULTILINGUAL
    template_fields = {
        "subject": forms.CharField(required=True, label=_(u"Subject")),
        "body_template": forms.CharField(
            required=False,
            label=_("Body Template"),
            help_text=_(
                "You can use this template to wrap the HTML body with your custom static template."
                "Mark the spot for the HTML body with %html_body%."
            ),
            widget=forms.Textarea()
        ),
        "body": forms.CharField(required=True, label=_("Email Body"), widget=TextEditorWidget()),
        "content_type": forms.ChoiceField(
            required=True, label=_(u"Content type"),
            choices=EMAIL_CONTENT_TYPE_CHOICES, initial=EMAIL_CONTENT_TYPE_CHOICES[0][0]
        )
    }

    from_email = Binding(
        _("From email"),
        type=Email,
        constant_use=ConstantUse.VARIABLE_OR_CONSTANT,
        required=False,
        help_text=_(
            'The from email to be used. It can either be binded to a variable or be a constant like '
            'support@store.com or even "Store Support" <support@store.com>.'
        )
    )
    recipient = Binding(_("Recipient"), type=Email, constant_use=ConstantUse.VARIABLE_OR_CONSTANT, required=True)
    reply_to_address = Binding(_("Reply-To"), type=Email, constant_use=ConstantUse.VARIABLE_OR_CONSTANT)
    language = Binding(_("Language"), type=Language, constant_use=ConstantUse.VARIABLE_OR_CONSTANT, required=True)
    fallback_language = Binding(
        _("Fallback language"), type=Language, constant_use=ConstantUse.CONSTANT_ONLY,
        default=settings.PARLER_DEFAULT_LANGUAGE_CODE
    )
    send_identifier = Binding(
        _("Send Identifier"), type=Text, constant_use=ConstantUse.CONSTANT_ONLY, required=False,
        help_text=_(
            "If set, this identifier will be logged into the event's log target. If the identifier has already "
            "been logged, the e-mail won't be sent again."
        )
    )

    def execute(self, context):
        """
        :param context: Script Context
        :type context: shuup.notify.script.Context
        """
        recipient = self.get_value(context, "recipient")
        if not recipient:
            context.log(logging.INFO, "%s: Not sending mail, no recipient", self.identifier)
            return

        send_identifier = self.get_value(context, "send_identifier")
        if send_identifier and context.log_entry_queryset.filter(identifier=send_identifier).exists():
            context.log(
                logging.INFO,
                "%s: Not sending mail, have sent it already (%r)",
                self.identifier,
                send_identifier
            )
            return

        languages = [language for language in [
            self.get_value(context, "language"),
            self.get_value(context, "fallback_language"),
        ] if language and language in dict(settings.LANGUAGES).keys()]

        if not languages:
            languages = [settings.PARLER_DEFAULT_LANGUAGE_CODE]

        strings = self.get_template_values(context, languages)

        subject = strings.get("subject")
        body = strings.get("body")
        body_template = strings.get("body_template")

        if body_template and "%html_body%" in body_template:
            body = body_template.replace("%html_body%", body)

        content_type = strings.get("content_type")
        if not (subject and body):
            context.log(
                logging.INFO,
                "%s: Not sending mail to %s, either subject or body empty",
                self.identifier,
                recipient
            )
            return

        reply_to = self.get_value(context, "reply_to_address")
        reply_to = [reply_to] if reply_to else None  # Push email to a list, unless it is None

        from_email = self.get_value(context, "from_email") or None
        subject = " ".join(subject.splitlines())  # Email headers may not contain newlines
        message = EmailMessage(subject=subject, body=body, to=[recipient], reply_to=reply_to, from_email=from_email)
        message.content_subtype = content_type
        message.send()
        context.log(logging.INFO, "%s: Mail sent to %s :)", self.identifier, recipient)

        if send_identifier:
            context.add_log_entry_on_log_target("Email sent to %s: %s" % (recipient, subject), send_identifier)
