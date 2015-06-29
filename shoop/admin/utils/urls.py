# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

try:
    from urllib.parse import parse_qsl
except ImportError:  # pragma: no cover
    from urlparse import parse_qsl  # Python 2.7

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import RegexURLPattern, get_callable, reverse, NoReverseMatch
from django.http.response import HttpResponseForbidden
from django.utils.encoding import force_text
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from shoop.admin.module_registry import get_modules
from shoop.utils.excs import Problem
import inspect
import json
import six


class AdminRegexURLPattern(RegexURLPattern):
    def __init__(self, regex, callback, default_args=None, name=None, require_authentication=True, permissions=()):
        self.permissions = tuple(permissions)
        self.require_authentication = require_authentication
        if callable(callback):
            callback = self.wrap_with_permissions(callback)
        super(AdminRegexURLPattern, self).__init__(regex, callback, default_args, name)

    def _get_unauth_response(self, request, reason):
        """
        Get an error response (or raise a Problem) for a given request and reason message.

        :type request: Request
        :param request: HttpRequest
        :type reason: Reason string
        :param reason: str
        """
        if request.is_ajax():
            return HttpResponseForbidden(json.dumps({"error": force_text(reason)}))
        resp = redirect_to_login(
            next=request.path,
            login_url="%s?%s" % (reverse("shoop_admin:login"), urlencode({"error": reason}))
        )
        if request.user.is_authenticated():
            # Instead of redirecting to the login page, let the user know what's wrong with
            # a helpful link.
            raise (
                Problem(_("Can't view this page. %(reason)s") % {"reason": reason})
                .with_link(url=resp.url, title=_("Log in with different credentials…"))
            )
        return resp

    def _get_unauth_reason(self, request):
        """
        Figure out if there's any reason not to allow the user access to this view via the given request.

        :type request: Request
        :param request: HttpRequest
        :rtype: str|None
        """

        if self.require_authentication:
            if not request.user.is_authenticated():
                return _("You must be logged in.")
            elif not request.user.is_staff:
                return _("You must be a staff member.")

        missing_permissions = set(p for p in set(self.permissions) if not request.user.has_perm(p))
        if missing_permissions:
            return _("You do not have the required permissions: %r") % missing_permissions

    def wrap_with_permissions(self, view_func):
        if callable(getattr(view_func, "as_view", None)):
            view_func = view_func.as_view()

        @six.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            unauth_reason = self._get_unauth_reason(request)
            if unauth_reason:
                return self._get_unauth_response(request, unauth_reason)
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    @property
    def callback(self):
        if self._callback is not None:
            return self._callback

        callback = get_callable(self._callback_str)
        self._callback = self.wrap_with_permissions(callback)
        return self._callback


def admin_url(regex, view, kwargs=None, name=None, prefix='', require_authentication=True, permissions=()):
    if isinstance(view, six.string_types):
        if not view:
            raise ImproperlyConfigured('Empty URL pattern view name not permitted (for pattern %r)' % regex)
        if prefix:
            view = prefix + '.' + view
    return AdminRegexURLPattern(
        regex, view, kwargs, name,
        require_authentication=require_authentication,
        permissions=permissions
    )


class NoModelUrl(ValueError):
    pass


def get_model_url(object, kind="detail"):
    """
    Get a an admin object URL for the given object or object class by interrogating
    each admin module.

    Raises `NoModelUrl` if lookup fails

    :param object: Model or object class.
    :type object: class
    :param kind: URL kind. Currently "new", "list", "edit", "detail".
    :type kind: str
    :return: Resolved URL.
    :rtype: str
    """
    for module in get_modules():
        url = module.get_model_url(object, kind)
        if url:
            return url
    raise NoModelUrl("Can't get object URL of kind %s: %r" % (kind, object))


def derive_model_url(model_class, urlname_prefix, object, kind):
    """
    Try to guess a model URL for the given `object` and `kind`.

    An utility for people implementing `get_model_url`.

    :param model_class: The model class the object must be an instance or subclass of.
    :type model_class: class
    :param urlname_prefix: URLname prefix. For instance, `shoop_admin:product.`
    :type urlname_prefix: str
    :param object: The model or model class as passed to `get_model_url`
    :type object: django.db.models.Model|class
    :param kind: URL kind as passed to `get_model_url`.
    :type kind: str
    :return: Resolved URL or None.
    :rtype: str|None
    """
    if not (isinstance(object, model_class) or (inspect.isclass(object) and issubclass(object, model_class))):
        return

    kind_to_urlnames = {
        "detail": ("%s.detail" % urlname_prefix, "%s.edit" % urlname_prefix),
    }

    kwarg_sets = [{}]
    if getattr(object, "pk", None):
        kwarg_sets.append({"pk": object.pk})

    for urlname in kind_to_urlnames.get(kind, ["%s.%s" % (urlname_prefix, kind)]):
        for kwargs in kwarg_sets:
            try:
                return reverse(urlname, kwargs=kwargs)
            except NoReverseMatch:
                pass
    # No match whatsoever.
    return None


def manipulate_query_string(url, **qs):
    if "?" in url:
        url, current_qs = url.split("?", 1)
        qs = dict(parse_qsl(current_qs), **qs)
    qs = [(key, value) for (key, value) in qs.items() if value is not None]
    if qs:
        return "%s?%s" % (url, urlencode(qs))
    else:
        return url


def get_model_front_url(request, object):
    """
    Get a frontend URL for an object.

    :param request: Request
    :type request: HttpRequest
    :param object: A model instance
    :type object: django.db.models.Model
    :return: URL or None
    :rtype: str|None
    """
    # TODO: This method could use an extension point for alternative frontends.
    if not object.pk:
        return None
    if "shoop.front" in settings.INSTALLED_APPS:
        # Best effort to use the default frontend for front URLs.
        try:
            from shoop.front.template_helpers.urls import model_url
            return model_url({"request": request}, object)
        except (ValueError, NoReverseMatch):
            pass
    return None
