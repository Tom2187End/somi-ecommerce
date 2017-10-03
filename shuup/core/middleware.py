# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http.response import JsonResponse
from django.shortcuts import render
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.core.shop_provider import get_shop
from shuup.utils.excs import ExceptionalResponse, Problem


class ExceptionMiddleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, ExceptionalResponse):
            return exception.response

        if isinstance(exception, (ValidationError, Problem)):
            if request.is_ajax():
                return JsonResponse({
                    "error": force_text(exception),
                    "code": getattr(exception, "code", None)
                })
            return render(request, self._get_problem_templates(request), {
                "title": getattr(exception, "title", None) or _("Error"),
                "message": exception.message,
                "exception": exception,
            })

    def _get_problem_templates(self, request):
        templates = []
        try:
            app_name = force_text(request.resolver_match.app_name)
            namespace = force_text(request.resolver_match.namespace)
            templates.extend([
                "%s/problem.jinja" % app_name,
                "%s/problem.jinja" % app_name.replace("_", "/"),
                "%s/problem.jinja" % namespace,
                "%s/problem.jinja" % namespace.replace("_", "/"),
            ])
        except (AttributeError, NameError):  # No resolver match? :(
            pass
        templates.extend([
            "shuup/front/problem.jinja",
            "problem.jinja",
            "problem.html",
        ])
        return templates


class ShuupMiddleware(object):
    """
    Handle Shuup specific tasks for each request and response.

    * Sets the current shop according to the host name
      ``request.shop`` : :class:`shuup.core.models.Shop`
          Currently active Shop.
    """

    def process_request(self, request):
        request.shop = get_shop(request)

        if not request.shop:
            raise ImproperlyConfigured(_("No shop!"))
