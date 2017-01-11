# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from registration.signals import user_registered

from shuup.notify.base import Event, Variable
from shuup.notify.script_template.factory import \
    generic_send_email_script_template_factory
from shuup.notify.typology import Email


class RegistrationReceived(Event):
    identifier = "registration_received"
    name = _("Registration Received")

    customer_email = Variable(_("Customer Email"), type=Email)


@receiver(user_registered)
def send_user_registered_notification(user, **kwargs):
    RegistrationReceived(
        customer_email=user.email,
    ).run()


RegistrationReceivedEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="registration_received_email",
    event=RegistrationReceived,
    name=_("Send Registration Received Email"),
    description=_("Send email when a user registers."),
    help_text=_("This script will send an email to the user or to any configured email "
                "right after a user get registered."),
    initial=dict(
        subject=_("{{ order.shop }} - Welcome!")
    )
)
