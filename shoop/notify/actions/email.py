# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import logging
from django import forms
from django.core.mail.message import EmailMessage
from shoop.notify.base import Action, Binding
from shoop.notify.enums import TemplateUse, ConstantUse
from django.utils.translation import ugettext as _
from shoop.notify.typology import Email, Text, Language


class SendEmail(Action):
    identifier = "send_email"
    template_use = TemplateUse.MULTILINGUAL
    template_fields = {
        "subject": forms.CharField(required=True, label=_(u"Subject")),
        "body": forms.CharField(required=True, label=_(u"Email Body"), widget=forms.Textarea()),
    }

    recipient = Binding(_("Recipient"), type=Email, constant_use=ConstantUse.VARIABLE_OR_CONSTANT, required=True)
    language = Binding(_("Language"), type=Language, constant_use=ConstantUse.VARIABLE_OR_CONSTANT, required=True)
    fallback_language = Binding(
        _("Fallback language"), type=Language, constant_use=ConstantUse.CONSTANT_ONLY, default="en"
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
        :type context: shoop.notify.script.Context
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
        ] if language]
        strings = self.get_template_values(context, languages)

        subject = strings.get("subject")
        body = strings.get("body")
        if not (subject and body):
            context.log(
                logging.INFO,
                "%s: Not sending mail to %s, either subject or body empty",
                self.identifier,
                recipient
            )
            return

        subject = " ".join(subject.splitlines())  # Email headers may not contain newlines
        message = EmailMessage(subject=subject, body=body, to=[recipient])
        message.send()
        context.log(logging.INFO, "%s: Mail sent to %s :)", self.identifier, recipient)

        if send_identifier:
            context.add_log_entry_on_log_target("Email sent to %s: %s" % (recipient, subject), send_identifier)
