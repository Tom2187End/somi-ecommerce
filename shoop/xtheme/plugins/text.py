# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import markdown
from django import forms
from django.utils.html import escape
from django.utils.safestring import mark_safe

from shoop.xtheme.plugins.base import Plugin


class TextPlugin(Plugin):
    """
    Very basic Markdown rendering plugin.
    """
    identifier = "text"
    name = "Text"
    fields = [
        ("text", forms.CharField(required=False, widget=forms.Textarea))
    ]

    def render(self, context):  # doccov: ignore
        text = (self.config.get("text") or "")
        try:
            markup = markdown.markdown(text)
        except:  # Markdown parsing error? Well, just escape then...
            markup = escape(text)
        return mark_safe(markup)
