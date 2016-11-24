# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

import six
from django.forms import HiddenInput, Widget
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from filer.models import File

from shuup.admin.utils.forms import flatatt_filter
from shuup.admin.utils.urls import get_model_url, NoModelUrl
from shuup.core.models import Contact, PersonContact, Product, ProductMode


class BasePopupChoiceWidget(Widget):
    browse_kind = None
    filter = None

    def __init__(self, attrs=None, clearable=False, empty_text=u"\u2014"):
        self.clearable = clearable
        self.empty_text = empty_text
        super(BasePopupChoiceWidget, self).__init__(attrs)

    def get_browse_markup(self):
        icon = "<i class='fa fa-folder'></i>"
        return "<button class='browse-btn btn btn-info btn-sm' type='button'>%(icon)s %(text)s</button>" % {
            "icon": icon,
            "text": _("Browse")
        }

    def get_clear_markup(self):
        icon = "<i class='fa fa-cross'></i>"
        return "<button class='clear-btn btn btn-default btn-sm' type='button'>%(icon)s %(text)s</button>" % {
            "icon": icon,
            "text": _("Clear")
        }

    def render_text(self, obj):
        url = getattr(obj, "url", None)
        text = self.empty_text
        if obj:
            text = force_text(obj)
            if not url:
                try:
                    url = get_model_url(obj)
                except NoModelUrl:
                    pass
        if not url:
            url = "#"

        return mark_safe("<a class=\"browse-text\" href=\"%(url)s\" target=\"_blank\">%(text)s</a>&nbsp;" % {
            "text": escape(text),
            "url": escape(url),
        })

    def get_object(self, value):
        raise NotImplementedError("Not implemented")

    def render(self, name, value, attrs=None):
        if value:
            obj = self.get_object(value)
        else:
            obj = None
        pk_input = HiddenInput().render(name, value, attrs)
        media_text = self.render_text(obj)
        bits = [self.get_browse_markup(), pk_input, " ", media_text]

        if self.clearable:
            bits.insert(1, self.get_clear_markup())

        return mark_safe("<div %(attrs)s>%(content)s</div>" % {
            "attrs": flatatt_filter({
                "class": "browse-widget %s-browse-widget" % self.browse_kind,
                "data-browse-kind": self.browse_kind,
                "data-clearable": self.clearable,
                "data-empty-text": self.empty_text,
                "data-filter": self.filter
            }),
            "content": "".join(bits)
        })


class FileDnDUploaderWidget(Widget):
    def __init__(self, attrs=None, kind=None, upload_path="/"):
        self.kind = kind
        self.upload_path = upload_path
        super(FileDnDUploaderWidget, self).__init__(attrs)

    def _get_file_attrs(self, file):
        try:
            thumbnail = file.easy_thumbnails_thumbnailer.get_thumbnail({
                'size': (120, 120),
                'crop': True,
                'upscale': True,
                'subject_location': file.subject_location
            })
        except Exception:
            thumbnail = None
        data = {
            "id": file.id,
            "name": file.label,
            "size": file.size,
            "url": file.url,
            "thumbnail": (thumbnail.url if thumbnail else None),
            "date": file.uploaded_at.isoformat()
        }
        return ["data-%s='%s'" % (key, val) for key, val in six.iteritems(data) if val is not None]

    def render(self, name, value, attrs={}):
        pk_input = HiddenInput().render(name, value, attrs)
        file_attrs = ["data-upload_path='%s'" % self.upload_path]
        if self.kind:
            file_attrs.append("data-kind='%s'" % self.kind)
        if value:
            file = File.objects.get(pk=value)
            file_attrs += self._get_file_attrs(file)
        return (
            mark_safe("<div id='%s-dropzone' class='dropzone %s' %s>%s</div>" % (
                attrs.get("id", "dropzone"),
                "has-file" if value else "",
                " ".join(file_attrs),
                pk_input
            ))
        )


class MediaChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "media"

    def get_object(self, value):
        return File.objects.get(pk=value)


class ImageChoiceWidget(MediaChoiceWidget):
    filter = "images"


class ProductChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "product"

    def get_object(self, value):
        return Product.objects.get(pk=value)


class ContactChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "contact"

    def get_object(self, value):
        return Contact.objects.get(pk=value)

    def get_browse_markup(self):
        icon = "<i class='fa fa-user'></i>"
        return "<button class='browse-btn btn btn-info btn-sm' type='button'>%(icon)s %(text)s</button>" % {
            "icon": icon,
            "text": _("Select")
        }


class PersonContactChoiceWidget(ContactChoiceWidget):

    @property
    def filter(self):
        return json.dumps({"groups": [PersonContact.get_default_group().pk]})


class PackageProductChoiceWidget(ProductChoiceWidget):
    filter = json.dumps({"modes": [ProductMode.NORMAL.value, ProductMode.VARIATION_CHILD.value]})
