# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.toolbar import DropdownItem, URLActionButton


class MockContactToolbarButton(URLActionButton):
    def __init__(self, contact, **kwargs):

        kwargs["icon"] = "fa fa-user"
        kwargs["text"] = _("Hello") + contact.full_name
        kwargs["extra_css_class"] = "btn-info"
        kwargs["url"] = "/#mocktoolbarbutton"

        self.contact = contact

        super(MockContactToolbarButton, self).__init__(**kwargs)


class MockContactToolbarActionItem(DropdownItem):
    def __init__(self, object, **kwargs):
        kwargs["icon"] = "fa fa-hand-peace-o"
        kwargs["text"] = _("Hello %(name)s") % {"name": object.full_name}
        kwargs["url"] = "/#mocktoolbaractionitem"
        super(MockContactToolbarActionItem, self).__init__(**kwargs)

    @staticmethod
    def visible_for_object(object):
        return True


class MockProductToolbarActionItem(DropdownItem):
    def __init__(self, object, **kwargs):
        kwargs["icon"] = "fa fa-female"
        kwargs["text"] = _("This is %(sku)s") % {"sku": object.sku}
        kwargs["url"] = "#%(sku)s" % {"sku": object.sku}
        super(MockProductToolbarActionItem, self).__init__(**kwargs)
