# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.utils.datastructures import OrderedDict
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup import configuration
from shuup.admin.module_registry import get_modules
from shuup.admin.utils.permissions import get_missing_permissions
from shuup.admin.views.home import QUICKLINK_ORDER
from shuup.apps.provides import get_provide_objects

ORDERS_MENU_CATEGORY = 1
PRODUCTS_MENU_CATEGORY = 2
CONTACTS_MENU_CATEGORY = 3
REPORTS_MENU_CATEGORY = 4
CAMPAIGNS_MENU_CATEGORY = 5
STOREFRONT_MENU_CATEGORY = 6
ADDONS_MENU_CATEGORY = 7
SETTINGS_MENU_CATEGORY = 8
CONTENT_MENU_CATEGORY = 9

MAIN_MENU = [
    {
        "identifier": ORDERS_MENU_CATEGORY,
        "title": _("Orders"),
        "icon": "fa fa-inbox",
    },
    {
        "identifier": PRODUCTS_MENU_CATEGORY,
        "title": _("Products"),
        "icon": "fa fa-cube",
    },
    {
        "identifier": CONTACTS_MENU_CATEGORY,
        "title": _("Contacts"),
        "icon": "fa fa-users",
    },
    {
        "identifier": CAMPAIGNS_MENU_CATEGORY,
        "title": _("Campaigns"),
        "icon": "fa fa-bullhorn",
    },
    {
        "identifier": CONTENT_MENU_CATEGORY,
        "title": _("Content"),
        "icon": "fa fa-columns",
    },
    {
        "identifier": REPORTS_MENU_CATEGORY,
        "title": _("Reports"),
        "icon": "fa fa-bar-chart",
    },
    {
        "identifier": STOREFRONT_MENU_CATEGORY,
        "title": _("Shops"),
        "icon": "fa fa-shopping-basket",
    },
    {
        "identifier": ADDONS_MENU_CATEGORY,
        "title": _("Addons"),
        "icon": "fa fa-puzzle-piece",
    },
    {
        "identifier": SETTINGS_MENU_CATEGORY,
        "title": _("Settings"),
        "icon": "fa fa-tachometer",
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
        self.is_hidden = False

    def __iter__(self):
        return iter(sorted(self.entries, key=lambda e: e.ordering))


def extend_main_menu(menu):
    for menu_updater in get_provide_objects("admin_main_menu_updater"):
        menu = menu_updater(menu).update()
    return menu


def get_menu_entry_categories(request): # noqa (C901)
    menu_categories = OrderedDict()

    # Update main menu from provides
    main_menu = extend_main_menu(MAIN_MENU)

    menu_category_icons = {}
    for menu_item in main_menu:
        identifier = menu_item["identifier"]
        icon = menu_item["icon"]
        menu_categories[identifier] = _MenuCategory(
            identifier=identifier,
            name=menu_item["title"],
            icon=icon,
        )
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
            entry_identifier = entry.url
            category = menu_categories.get(entry.category)
            if not category:
                category_identifier = force_text(entry.category or module.name)
                category = menu_categories.get(category_identifier)
                if not category:
                    menu_categories[category_identifier] = category = _MenuCategory(
                        identifier=category_identifier,
                        name=category_identifier,
                        icon=menu_category_icons.get(category_identifier, "fa fa-circle")
                    )
            category.entries.append(entry)
            all_categories.add(category)

    # clean categories that eventually have no children or entries
    categories = []
    for cat in all_categories:
        if not cat.entries:
            continue
        categories.append(cat)
    clean_categories = [c for menu_identifier, c in six.iteritems(menu_categories) if c in categories]

    def pop_category(identifier):
        for index, clean_category in enumerate(clean_categories):
            if clean_category.identifier == identifier:
                category = clean_categories.pop(index)
                return category
            else:
                for sub_index, sub_category in enumerate(clean_category.children):
                    if sub_category.identifier == identifier:
                        category = clean_category.children.pop(sub_index)
                        return category

    customized_admin_menu = configuration.get(None, "admin_menu_user_{}".format(request.user.pk))
    if customized_admin_menu:
        customized_categories = []
        # override default values from admin_menu configuration
        for admin_menu in customized_admin_menu:
            category = pop_category(admin_menu["identifier"])
            if category:
                category.name = admin_menu.get("name", category.name)
                category.is_hidden = admin_menu.get("is_hidden", False)

                for sub_admin_menu in admin_menu.get("children", []):
                    sub_category = pop_category(sub_admin_menu["identifier"])
                    if not sub_category:
                        for sub_index, clean_category in enumerate(category.children):
                            if clean_category.identifier == sub_admin_menu["identifier"]:
                                sub_category = category.children.pop(sub_index)

                    if sub_category:
                        sub_category.name = sub_admin_menu.get("name", sub_category.name)
                        sub_category.is_hidden = sub_admin_menu.get("is_hidden", False)
                        category.children.append(sub_category)

                customized_categories.append(category)

        return customized_categories + clean_categories
    else:
        return clean_categories


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
