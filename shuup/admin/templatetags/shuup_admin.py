# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import django_jinja
from bootstrap3.renderers import FormRenderer
from django.utils.safestring import mark_safe
from django_jinja import library

from shuup.admin.shop_provider import get_shop
from shuup.admin.template_helpers import shuup_admin as shuup_admin_template_helpers
from shuup.admin.utils.bs3_renderers import AdminFieldRenderer
from shuup.xtheme.models import AdminThemeSettings


class Bootstrap3Namespace(object):
    def field(self, field, **kwargs):
        if not field:
            return ""
        return mark_safe(AdminFieldRenderer(field, **kwargs).render())

    def form(self, form, **kwargs):
        return mark_safe(FormRenderer(form, **kwargs).render())


library.global_function(name="shuup_admin", fn=shuup_admin_template_helpers)
library.global_function(name="bs3", fn=Bootstrap3Namespace())


@django_jinja.library.global_function
def get_current_admin_theme(request):
    """Return the set admin theme"""
    return AdminThemeSettings.objects.filter(shop=get_shop(request)).first()


def clamp(val, minimum=0, maximum=255):
    if val < minimum:
        return minimum
    if val > maximum:
        return maximum
    return val


@django_jinja.library.global_function
def colorscale(hexstr, scalefactor):
    """
    Scales a hex string by ``scalefactor``. Returns scaled hex string.

    To darken the color, use a float value between 0 and 1.
    To brighten the color, use a float value greater than 1.

    >>> colorscale("#DF3C3C", .5)
    #6F1E1E
    >>> colorscale("#52D24F", 1.6)
    #83FF7E
    >>> colorscale("#4F75D2", 1)
    #4F75D2
    """

    hexstr = hexstr.strip("#")

    if scalefactor < 0 or len(hexstr) != 6:
        return hexstr

    r, g, b = int(hexstr[:2], 16), int(hexstr[2:4], 16), int(hexstr[4:], 16)

    r = clamp(int(r * scalefactor))
    g = clamp(int(g * scalefactor))
    b = clamp(int(b * scalefactor))

    return "#%02x%02x%02x" % (r, g, b)
