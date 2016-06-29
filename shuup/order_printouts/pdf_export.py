# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os
import urllib

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from easy_thumbnails.files import get_thumbnailer

from shuup.utils.excs import Problem

try:
    import weasyprint
except ImportError:
    weasyprint = None


def _fetch_static_resource_str(resource_file):
    resource_path = os.path.realpath(os.path.join(settings.STATIC_ROOT, resource_file))
    if not resource_path.startswith(settings.STATIC_ROOT):
        raise ValueError(
            "Possible file system traversal shenanigan detected with %(path)s" % {"path": resource_file})

    if not os.path.isfile(resource_path):
        from django.contrib.staticfiles import finders
        resource_path = finders.find(resource_file)

    if not resource_path:
        raise ValueError("Unable to find: %(path)s" % {"path": resource_file})

    return open(resource_path, "rb").read().decode("UTF-8", "replace")


def _custom_url_fetcher(url):
    if url.startswith("logo:"):
        thumbnailer = get_thumbnailer(urllib.unquote(url[5:]))
        thumbnail_options = {"size": (240, 80), "upscale": True}
        return {"file_obj": thumbnailer.get_thumbnail(thumbnail_options), "mime_type": "image/jpg"}
    raise ValueError("Possible file system traversal shenanigan detected with %(path)s" % {"path": url})


def render_html_to_pdf(html, stylesheet_paths=[]):
    if not weasyprint:
        raise Problem(_("Could not create PDF since Weasyprint is not available. Please contact support."))
    stylesheets = []
    for stylesheet_path in stylesheet_paths:
        stylesheets.append(weasyprint.CSS(string=_fetch_static_resource_str(stylesheet_path)))
    pdf = weasyprint.HTML(
        string=html, url_fetcher=_custom_url_fetcher
    ).write_pdf(
        stylesheets=stylesheets
    )
    return wrap_pdf_in_response(pdf)


def wrap_pdf_in_response(pdf_data):
    response = HttpResponse(content_type='application/pdf')
    response.write(pdf_data)
    return response
