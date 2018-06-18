# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import re

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.transaction import atomic
from django.http import (
    HttpResponse, HttpResponseNotFound, HttpResponseRedirect
)
from django.utils.text import force_text
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, View

from shuup.core.models import get_person_contact, Order
from shuup.front.views.dashboard import DashboardViewMixin
from shuup.gdpr.models import (
    GDPR_ANONYMIZE_TASK_TYPE_IDENTIFIER, GDPRCookieCategory
)
from shuup.gdpr.utils import (
    add_consent_to_response_cookie, get_cookie_consent_data
)
from shuup.utils.analog import LogEntryKind
from shuup.utils.djangoenv import has_installed

COOKIE_CONSENT_RE = r"cookie_category_(\d+)"


class GDPRCookieConsentView(View):
    def post(self, request, *args, **kwargs):
        shop = request.shop
        cookie_categories = list(GDPRCookieCategory.objects.filter(shop=shop, always_active=True))

        for field, value in request.POST.items():
            field_match = re.match(COOKIE_CONSENT_RE, field)
            if field_match and value.lower() in ["on", "1"]:
                cookie_category = GDPRCookieCategory.objects.filter(shop=shop, id=field_match.groups()[0]).first()
                if cookie_category:
                    cookie_categories.append(cookie_category)

        consent_documents = []
        if has_installed("shuup.simple_cms"):
            from shuup.simple_cms.models import Page, PageType
            consent_documents = Page.objects.visible(shop).filter(page_type=PageType.REVISIONED)

        cookie_data = get_cookie_consent_data(cookie_categories, consent_documents)

        if request.META.get("HTTP_REFERER"):
            redirect_url = request.META["HTTP_REFERER"]
        else:
            redirect_url = force_text(reverse("shuup:index"))

        response = HttpResponseRedirect(redirect_url)
        add_consent_to_response_cookie(response, cookie_data)
        return response


class GDPRCustomerDashboardView(DashboardViewMixin, TemplateView):
    template_name = "shuup/gdpr/edit_customer_data.jinja"

    def get_context_data(self, **kwargs):
        context = super(GDPRCustomerDashboardView, self).get_context_data(**kwargs)
        has_peding_orders = False

        if Order.objects.incomplete().filter(customer=self.request.person).exists():
            has_peding_orders = True
        else:
            for company in self.request.person.company_memberships.all():
                if company.members.count() == 1:
                    has_peding_orders = True

        context["has_peding_orders"] = has_peding_orders
        return context


class GDPRDownloadDataView(View):
    def post(self, request, *args, **kwargs):
        if not self.request.person:
            return HttpResponseNotFound()

        self.request.person.add_log_entry(
            "User personal data download requested", kind=LogEntryKind.NOTE, user=self.request.user)

        from shuup.gdpr.utils import get_all_contact_data
        data = json.dumps(get_all_contact_data(self.request.person))
        response = HttpResponse(data, content_type="application/json")
        response["Content-Disposition"] = "attachment; filename=user_data.json"
        return response


class GDPRAnonymizeView(View):
    def post(self, request, *args, **kwargs):
        if not request.person:
            return HttpResponseNotFound()

        self.request.person.add_log_entry(
            "User anonymization requested", kind=LogEntryKind.NOTE, user=request.user)

        with atomic():
            from shuup.tasks.models import TaskType
            from shuup.tasks.utils import create_task
            task_type = TaskType.objects.get_or_create(
                shop=request.shop,
                identifier=GDPR_ANONYMIZE_TASK_TYPE_IDENTIFIER,
                defaults=dict(name=_("GDPR: Anonymize"))
            )[0]
            contact = get_person_contact(request.user)
            create_task(
                request.shop,
                contact,
                task_type,
                _("GDPR: Anonymize contact"),
                _("Customer ID {customer_id} requested to be anonymized.").format(**dict(customer_id=contact.id))
            )

            contact.is_active = False
            contact.save()
            request.user.is_active = False
            request.user.save()
            messages.success(request, _("Anonymization requested."))

        return HttpResponseRedirect(reverse("shuup:index"))
