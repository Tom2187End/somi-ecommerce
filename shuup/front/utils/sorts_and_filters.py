# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import abc

import six
from django import forms
from django.conf import settings
from django.db.models import Q

from shuup import configuration
from shuup.apps.provides import get_provide_objects

FACETED_DEFAULT_CONF_KEY = "front_faceted_configurations"
FACETED_CATEGORY_CONF_KEY_PREFIX = "front_faceted_category_configurations_%s"
FORM_MODIFIER_PROVIDER_KEY = "front_extend_product_list_form"


class ProductListFormModifier(six.with_metaclass(abc.ABCMeta)):

    """
    Interface class for modifying product lists

    This interface can be used to sort and filter product lists in
    category and search view.

    By subclassing this interface the ProductListForm fields can be
    added. Also this interface provides methods for sorting and
    filtering product lists.
    """

    def should_use(self, configuration):
        """
        :param configuration: current configurations
        :type configuration: dict
        :return: Boolean whether the modifier should be used based
        on current configurations.
        :rtype: boolean
        """
        return False

    def get_ordering(self, configuration):
        """
        :param configuration: current configurations
        :type configuration: dict
        :return: Ordering value based on configurations
        :rtype: int
        """
        pass

    def get_fields(self, category=None):
        """
        Extra fields for product list form.

        :param category: Current category
        :type category: shuup.core.models.Category|None
        :return: List of extra fields that should be added to form.
        Tuple should contain field name and Django form field.
        :rtype: list[(str,django.forms.Field)]
        """
        pass

    def get_choices_for_fields(self):
        """
        Provide sort choices for product list form

        :return: List of sort choices that should be added for form
        sort field. Tuple should contain sort key and label name.
        :rtype: list[(str,str)]
        """
        pass

    def sort_products(self, request, products, sort):
        """
        Sort products in case sort choices is provided

        Sort products in cse the list should be sorted based on
        sort choice provided by this class.

        :param request: Current request
        :param products: Products to sort
        :type products: list[shuup.code.models.Product]
        :param sort: Key to sort with
        :type sort: str
        :return: List of products that might be sorted
        :rtype: list[shuup.code.models.Product]
        """
        return products

    def get_filters(self, request, data):
        """
        Get filters based for the product list view

        Add Django query filters for Product queryset based
        on current request and ProductListForm data.

        :param request: current request
        :param data: Data from ProductListForm
        :type data: dict
        :return: Django query filter that can be used to
        filter Product queryset.
        :rtype: django.db.models.Q`
        """
        pass

    def filter_products(self, request, products, data):
        """
        Filter product objects

        Filtering products list based on current request and
        ProductListForm data.

        :param request:
        :param products: List of products
        :rtype products: list[shuup.core.models.Product]
        :param data: Data from ProductListForm
        :type data: dict
        :return: Filtered product list
        :rtype: list[shuup.core.models.Product]
        """
        return products

    def get_admin_fields(self):
        """
        Admin fields for sorts and filters configurations

        Adds fields for sorts and filters admin configuration
        form.

        :return: List of fields that should be added to form.
        Tuple should contain field name and Django form field.
        :rtype: list[(str,django.forms.Field)]
        """
        pass

    def clean_hook(self, form):
        """
        Extra clean for product list form.

        This hook will be called in `~Django.forms.Form.clean` method of
        the form, after calling parent clean.  Implementor of this hook
        may call `~Django.forms.Form.add_error` to add errors to form or
        modify the ``form.cleaned_data`` dictionary.

        :param form: Form that is currently cleaned
        :type form: ProductListForm
        :rtype: None
        """
        pass


class ProductListForm(forms.Form):
    def __init__(self, shop, category, *args, **kwargs):
        super(ProductListForm, self).__init__(*args, **kwargs)
        for extend_obj in _get_active_modifiers(shop, category):
            for field_key, field in extend_obj.get_fields(category) or []:
                if field_key not in self.fields:
                    self.fields[field_key] = field

            for field_key, choices in extend_obj.get_choices_for_fields() or []:
                if field_key in self.fields:
                    self.fields[field_key].widget.choices += choices

    def clean(self):
        cleaned_data = super(ProductListForm, self).clean()
        for extend_class in get_provide_objects(FORM_MODIFIER_PROVIDER_KEY):
            extend_class().clean_hook(self)
        return cleaned_data


def get_configuration(shop=None, category=None):
    default_configuration = configuration.get(
        shop, FACETED_DEFAULT_CONF_KEY, settings.SHUUP_FRONT_DEFAULT_SORT_CONFIGURATION)
    return (configuration.get(None, _get_category_configuration_key(category)) or default_configuration)


def set_configuration(shop=None, category=None, data=None):
    if category and category.pk:
        configuration.set(None, _get_category_configuration_key(category), data)
    elif shop:
        configuration.set(shop, FACETED_DEFAULT_CONF_KEY, data)


def get_query_filters(request, category, data):
    filter_q = Q()
    for extend_obj in _get_active_modifiers(request.shop, category):
        extra_filter = extend_obj.get_filters(request, data)
        if extra_filter:
            filter_q &= extra_filter
    return filter_q


def post_filter_products(request, category, products, data):
    for extend_obj in _get_active_modifiers(request.shop, category):
        products = extend_obj.filter_products(request, products, data)
    return products


def sort_products(request, category, products, data):
    sort = data.get("sort", "name_a")
    for extend_obj in _get_active_modifiers(request.shop, category):
        products = extend_obj.sort_products(request, products, sort)
    return products


def _get_category_configuration_key(category):
    return (FACETED_CATEGORY_CONF_KEY_PREFIX % category.pk if category and category.pk else None)


def _get_active_modifiers(shop=None, category=None):
    configuration = get_configuration(shop=shop, category=category)

    def sorter(extend_obj):
        return extend_obj.get_ordering(configuration)

    objs = []
    for cls in get_provide_objects(FORM_MODIFIER_PROVIDER_KEY):
        obj = cls()
        if obj.should_use(configuration):
            objs.append(obj)

    return sorted(objs, key=sorter)
