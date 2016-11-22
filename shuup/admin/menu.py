# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.utils.datastructures import OrderedDict
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.module_registry import get_modules
from shuup.admin.utils.permissions import get_missing_permissions
from shuup.admin.views.home import QUICKLINK_ORDER

ORDERS_MENU_CATEGORY = 1
PRODUCTS_MENU_CATEGORY = 2
CONTACTS_MENU_CATEGORY = 3
REPORTS_MENU_CATEGORY = 4
CAMPAIGNS_MENU_CATEGORY = 5
STOREFRONT_MENU_CATEGORY = 6
ADDONS_MENU_CATEGORY = 7
SETTINGS_MENU_CATEGORY = 8


MAIN_MENU = [
    {
        "identifier": ORDERS_MENU_CATEGORY,
        "title": _("Orders"),
        "icon": "fa fa-inbox",
        "children": []
    },
    {
        "identifier": PRODUCTS_MENU_CATEGORY,
        "title": _("Products"),
        "icon": "fa fa-cube",
        "children": []
    },
    {
        "identifier": CONTACTS_MENU_CATEGORY,
        "title": _("Contacts"),
        "icon": "fa fa-users",
        "children": []
    },
    {
        "identifier": REPORTS_MENU_CATEGORY,
        "title": _("Reports"),
        "icon": "fa fa-bar-chart",
        "children": []
    },
    {
        "identifier": CAMPAIGNS_MENU_CATEGORY,
        "title": _("Campaigns"),
        "icon": "fa fa-bullhorn",
        "children": []
    },
    {
        "identifier": STOREFRONT_MENU_CATEGORY,
        "title": _("Storefront"),
        "icon": "fa fa-paint-brush",
        "children": []
    },
    {
        "identifier": ADDONS_MENU_CATEGORY,
        "title": _("Addons"),
        "icon": "fa fa-puzzle-piece",
        "children": []
    },
    {
        "identifier": SETTINGS_MENU_CATEGORY,
        "title": _("Settings"),
        "icon": "fa fa-tachometer",
        "children": [
            {
                "identifier": "payment_shipping",
                "title": _("Payment & Shipping")
            },
            {
                "identifier": "store",
                "title": _("Storefront")
            },
            {
                "identifier": "taxes",
                "title": _("Taxes")
            }
        ]
    }
]


class _MenuCategory(object):
    """
    Internal menu category object.
    """
    def __init__(self, identifier, name, icon):
        self.identifier = identifier
        self.name = name
        self.icon = icon
        self.children = []
        self.entries = []

    def __iter__(self):
        return iter(sorted(self.entries, key=lambda e: e.ordering))


def get_menu_entry_categories(request):
    menu_categories = OrderedDict()
    menu_children = OrderedDict()

    menu_category_icons = {}
    for menu_item in MAIN_MENU:
        identifier = menu_item["identifier"]
        icon = menu_item["icon"]
        menu_categories[identifier] = _MenuCategory(
            identifier=identifier,
            name=menu_item["title"],
            icon=icon,
        )
        for child in menu_item["children"]:
            child_category = _MenuCategory(child["identifier"], child["title"], None)
            menu_children[child["identifier"]] = child_category
            menu_categories[identifier].children.append(child_category)

        menu_category_icons[identifier] = icon

    modules = list(get_modules())
    for module in modules:
        menu_category_icons.update(
            (force_text(key), force_text(value))
            for (key, value) in module.get_menu_category_icons().items()
            if key not in menu_category_icons
        )

    all_categories = set()
    for module in modules:
        if get_missing_permissions(request.user, module.get_required_permissions()):
            continue

        for entry in (module.get_menu_entries(request=request) or ()):
            category_identifier = entry.category
            subcategory = entry.subcategory

            entry_identifier = subcategory if subcategory else category_identifier
            menu_items = menu_children if subcategory else menu_categories

            category = menu_items.get(entry_identifier) if identifier else None
            if not category:
                category_identifier = force_text(category_identifier or module.name)
                category = menu_items.get(category_identifier)
                if not category:
                    menu_items[category_identifier] = category = _MenuCategory(
                        identifier=category_identifier,
                        name=category_identifier,
                        icon=menu_category_icons.get(category_identifier, "fa fa-circle")
                    )
            category.entries.append(entry)
            if subcategory:
                parent = menu_categories.get(category_identifier)
                all_categories.add(parent)
            else:
                all_categories.add(category)

    return [c for menu_identifier, c in six.iteritems(menu_categories) if c in all_categories]


def get_quicklinks(request):
    quicklinks = OrderedDict()
    for block in QUICKLINK_ORDER:
        quicklinks[block] = []

    for module in get_modules():
        if get_missing_permissions(request.user, module.get_required_permissions()):
            continue
        for help_block in module.get_help_blocks(request, kind="quicklink"):
            quicklinks[help_block.category].append(help_block)

    links = quicklinks.copy()
    for block, data in six.iteritems(links):
        if not quicklinks[block]:
            quicklinks.pop(block)
    return quicklinks
