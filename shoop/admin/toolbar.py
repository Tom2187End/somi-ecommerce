# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

import six
from django.core.urlresolvers import NoReverseMatch, reverse
from django.forms.utils import flatatt
from django.middleware.csrf import get_token
from django.utils.encoding import force_text
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from shoop.admin.utils.urls import NoModelUrl, get_model_url


def flatatt_filter(attrs):
    attrs = dict(
        (key, value)
        for (key, value)
        in six.iteritems(attrs)
        if key and value
    )
    return flatatt(attrs)


class BaseActionButton(object):
    base_css_classes = ("btn",)

    def __init__(self, text="", icon=None, disable_reason=None, tooltip=None, extra_css_class="btn-default"):
        """
        :param text: The actual text for the button.
        :param icon: Icon CSS class string
        :param disable_reason: The reason for this button to be disabled.
                               It's considered good UX to have an user-visible reason for disabled
                               actions; thus the only way to disable an action is to set the reason.
                               See http://stackoverflow.com/a/372503/51685.
        :type disable_reason: str|None
        :param tooltip: Tooltip string, if any. May be replaced by the disable reason.
        :type tooltip: str|None
        :param extra_css_class: Extra CSS class(es)
        :type extra_css_class: str
        """
        self.text = text
        self.icon = icon
        self.disable_reason = disable_reason
        self.disabled = bool(self.disable_reason)
        self.tooltip = (self.disable_reason or tooltip)
        self.extra_css_class = extra_css_class

    def render(self, request):
        """
        Yield HTML bits for this object.
        :type request: HttpRequest
        :rtype: Iterable[str]
        """
        return ()

    def render_label(self):
        bits = []
        if self.icon:
            bits.append('<i class="%s"></i>&nbsp;' % self.icon)
        bits.append(conditional_escape(self.text))
        return "".join(force_text(bit) for bit in bits)

    def get_computed_class(self):
        return " ".join(filter(None, list(self.base_css_classes) + [
            self.extra_css_class,
            "disabled" if self.disabled else ""
        ]))


class URLActionButton(BaseActionButton):
    """
    An action button that renders as a link leading to `url`.
    """

    def __init__(self, url, **kwargs):
        """
        :param url: The URL to navigate to. For convenience, if this contains no slashes,
                    `reverse` is automatically called on it.
        :type url: str
        """
        if "/" not in url:
            try:
                url = reverse(url)
            except NoReverseMatch:
                pass
        self.url = url
        super(URLActionButton, self).__init__(**kwargs)

    def render(self, request):
        yield '<a %s>' % flatatt_filter({
            "href": self.url,
            "class": self.get_computed_class(),
            "title": self.tooltip
        })
        yield self.render_label()
        yield '</a>'


class NewActionButton(URLActionButton):
    """
    An URL button with sane "new" visual semantics
    """

    def __init__(self, url, **kwargs):
        kwargs.setdefault("icon", "fa fa-plus")
        kwargs.setdefault("text", _("Create new"))
        kwargs.setdefault("extra_css_class", "btn-success")
        super(NewActionButton, self).__init__(url, **kwargs)

    @classmethod
    def for_model(cls, model, **kwargs):
        """
        Generate a NewActionButton for a model, auto-wiring the URL.

        :param model: Model class
        :rtype: shoop.admin.toolbar.NewActionButton|None
        """

        if "url" not in kwargs:
            try:
                url = get_model_url(model, kind="new")
            except NoModelUrl:
                return None
            kwargs["url"] = url
        kwargs.setdefault("text", _("New %(model)s") % {"model": model._meta.verbose_name})
        return cls(**kwargs)


class JavaScriptActionButton(BaseActionButton):
    """
    An action button that uses `onclick` for action dispatch.
    """

    def __init__(self, onclick, **kwargs):
        self.onclick = onclick
        super(JavaScriptActionButton, self).__init__(**kwargs)

    def render(self, request):
        yield '<a %s>' % flatatt_filter({
            "href": "#",
            "class": self.get_computed_class(),
            "title": self.tooltip,
            "onclick": mark_safe(self.onclick) if self.onclick else None
        })
        yield self.render_label()
        yield '</a>'


class PostActionButton(BaseActionButton):
    """
    An action button that renders as a button POSTing a form
    containing `name`=`value` to `post_url`.
    """

    def __init__(self, post_url=None, name=None, value=None, form_id=None, confirm=None, **kwargs):
        self.post_url = post_url
        self.name = name
        self.value = value
        self.form_id = form_id
        self.confirm = confirm
        super(PostActionButton, self).__init__(**kwargs)

    def render(self, request):
        yield '<button %s>' % flatatt_filter({
            "form": self.form_id,  # This can be used to post another form
            "formaction": self.post_url,
            "name": self.name,
            "value": self.value,
            "type": "submit",
            "title": self.tooltip,
            "class": self.get_computed_class(),
            "onclick": ("return confirm(%s)" % json.dumps(force_text(self.confirm)) if self.confirm else None)
        })
        yield self.render_label()
        yield '</button>'


class DropdownActionButton(BaseActionButton):
    """
    An action button with a chevron button to open a dropdown
    menu.
    """

    base_css_classes = ("btn", "dropdown-toggle")

    def __init__(self, items, split_button=None, **kwargs):
        self.split_button = split_button
        self.items = list(items)
        super(DropdownActionButton, self).__init__(**kwargs)

    def render_dropdown(self, request):
        yield '<ul class="dropdown-menu" role="menu">'
        for item in self.items:
            for bit in item.render(request):
                yield bit
        yield '</ul>'

    def render(self, request):
        yield '<div class="btn-group" role="group">'

        if self.split_button:
            for bit in self.split_button.render(request):
                yield bit

        yield '<button %s>' % flatatt_filter({
            "type": "button",
            "class": self.get_computed_class(),
            "data-toggle": "dropdown",
            "title": self.tooltip
        })

        if not self.split_button:
            yield self.render_label()
            yield " "

        yield '<i class="fa fa-chevron-down"></i>'
        yield '</button>'
        for bit in self.render_dropdown(request):
            yield bit
        yield '</div>'


class DropdownItem(BaseActionButton):
    """
    An item to be shown in a `DropdownActionButton`.
    """
    base_css_classes = ()

    def __init__(self, url="#", onclick=None, **kwargs):
        self.url = url
        self.onclick = onclick
        super(DropdownItem, self).__init__(**kwargs)

    def render(self, request):
        yield '<li>'
        attrs = {
            "class": self.get_computed_class(),
            "title": self.tooltip,
            "href": self.url,
            "onclick": (mark_safe(self.onclick) if self.onclick else None)
        }
        yield '<a %s>' % flatatt_filter(attrs)
        yield self.render_label()
        yield '</a>'
        yield '</li>'


class DropdownDivider(BaseActionButton):
    """
    A Divider for DropdownActionButtons.
    """
    base_css_classes = ()

    def render(self, request):
        yield '<li class="divider"></li>'


class DropdownHeader(BaseActionButton):
    """
    Header for DropdownActionButtons.
    """
    base_css_classes = ()

    def render(self, request):
        yield '<li class="dropdown-header">%s</li>' % self.text


# -----------

class ButtonGroup(list):
    def render(self, request):
        yield '<div class="btn-group" role="group">'
        for button in self:
            if button:
                if callable(button):  # Buttons may be functions/other callables too
                    yield button(request)
                else:
                    for bit in button.render(request):
                        yield bit
        yield '</div>'


class Toolbar(list):
    def render(self, request):
        # The toolbar is wrapped in a form without an action,
        # but `PostActionButton`s use the HTML5 `formaction` attribute.
        yield '<div class="shoop-toolbar">'
        yield '<form method="POST">'
        yield format_html("<input type='hidden' name='csrfmiddlewaretoken' value='{0}'>", get_token(request))
        yield '<div class="btn-toolbar" role="toolbar">'

        for group in self:
            if group:
                for bit in group.render(request):
                    yield bit

        yield '</div></form></div>'

    def render_to_string(self, request):
        return "".join(force_text(bit) for bit in self.render(request))


def try_reverse(viewname, **kwargs):
    try:
        return reverse(viewname, kwargs=kwargs)
    except NoReverseMatch:
        return viewname


def get_discard_button(discard_url):
    return URLActionButton(
        url=discard_url,
        text=_(u"Discard Changes"),
        icon="fa fa-undo",
        extra_css_class="btn-gray btn-inverse"
    )


def get_default_edit_toolbar(
        view_object, save_form_id,
        discard_url=None,
        delete_url=None,
        with_split_save=True,
        toolbar=None
):
    """
    Get a toolbar with buttons used for object editing.

    :param view_object: The class-based-view object requiring the toolbar
    :type view_object: django.views.generic.UpdateView
    :param save_form_id: The DOM ID to target for the save button
    :type save_form_id: str
    :param discard_url: The URL/route name for the Discard button. Falsy values default to the request URL.
    :type discard_url: str|None
    :param delete_url: The URL/route name for the Delete button. If this is not set, the delete button is not shown.
    :type delete_url: str|None
    :param with_split_save: Use split delete button with "Save and Exit" etc.?
    :type with_split_save: bool
    :param toolbar: The toolbar to augment. If None, a new one is created.
    :type toolbar: Toolbar
    :return: Toolbar
    :rtype: Toolbar
    """
    request = view_object.request
    object = view_object.object
    discard_url = (discard_url or request.path)
    toolbar = (Toolbar() if toolbar is None else toolbar)

    default_save_button = PostActionButton(
        icon="fa fa-save",
        form_id=save_form_id,
        text=_("Save"),
        extra_css_class="btn-success",
    )

    if with_split_save:
        save_dropdown = DropdownActionButton([
            DropdownItem(onclick="setNextActionAndSubmit('%s', 'return')" % save_form_id, text=_("Save and Exit")),
            DropdownItem(onclick="setNextActionAndSubmit('%s', 'new')" % save_form_id, text=_("Save and Create New")),
        ], split_button=default_save_button, extra_css_class="btn-success")
        toolbar.append(save_dropdown)
    else:
        toolbar.append(default_save_button)

    if object.pk:
        if discard_url:
            toolbar.append(get_discard_button(try_reverse(discard_url, pk=object.pk)))
        if delete_url:
            delete_url = try_reverse(delete_url, pk=object.pk)
            toolbar.append(PostActionButton(
                post_url=delete_url,
                text=_(u"Delete"),
                icon="fa fa-trash",
                extra_css_class="btn-danger btn-inverse",
                confirm=_("Are you sure you wish to delete %s?") % object
            ))

    # TODO: Add extensibility

    return toolbar
