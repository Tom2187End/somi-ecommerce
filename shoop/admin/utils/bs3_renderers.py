# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from bootstrap3.renderers import FieldRenderer
from bootstrap3.utils import add_css_class
from django.forms.models import ModelMultipleChoiceField
from django.utils.html import escape


class AdminFieldRenderer(FieldRenderer):

    def __init__(self, field, **kwargs):
        self.render_label = bool(kwargs.pop("render_label", True))
        self.set_placeholder = bool(kwargs.pop("set_placeholder", True))
        self.widget_class = kwargs.pop("widget_class", None)
        default_show_help_block = True
        if isinstance(field, ModelMultipleChoiceField):
            default_show_help_block = False
        self.show_help_block = bool(kwargs.pop("show_help_block", default_show_help_block))

        kwargs["required_css_class"] = "required-field"
        kwargs["set_required"] = False
        kwargs["bound_css_class"] = " "  # This is a hack, but Django-Bootstrap is silly and requires a truthy value.
        super(AdminFieldRenderer, self).__init__(field, **kwargs)
        if not self.set_placeholder:
            self.placeholder = None

    def get_label(self):
        if not self.render_label:
            return None
        return super(AdminFieldRenderer, self).get_label()

    def add_class_attrs(self):
        super(AdminFieldRenderer, self).add_class_attrs()
        if self.widget_class:
            classes = self.widget.attrs.get('class', '')
            classes = add_css_class(classes, self.widget_class)
            self.widget.attrs['class'] = classes

    def add_help_attrs(self):
        super(AdminFieldRenderer, self).add_help_attrs()
        if self.widget.attrs.get("title"):
            # The title attribute may contain quotes (notably the help for `ModelMultipleChoiceField`)
            # so ensure they are escaped
            self.widget.attrs["title"] = escape(self.widget.attrs["title"])
        else:
            self.widget.attrs.pop("title", None)  # Remove the empty attribute

        if not self.show_help_block:  # Remove field help to avoid rendering `help-block`
            self.field_help = ''
