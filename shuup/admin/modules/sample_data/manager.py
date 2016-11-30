# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup import configuration

SAMPLE_PRODUCTS_KEY = "sample_products"
SAMPLE_CATEGORIES_KEY = "sample_categories"
SAMPLE_CMS_PAGES_KEY = "sample_cms_pages"


def get_installed_products(shop):
    """ Returns the installed products samples list """
    return configuration.get(shop, SAMPLE_PRODUCTS_KEY) or []


def get_installed_categories(shop):
    """ Returns the installed categories samples list """
    return configuration.get(shop, SAMPLE_CATEGORIES_KEY) or []


def get_installed_cms_pages(shop):
    """ Returns the installed cms pages samples list """
    return configuration.get(shop, SAMPLE_CMS_PAGES_KEY) or []


def clear_installed_samples(shop):
    """ Clears all the samples values from the configuration """
    configuration.set(shop, SAMPLE_PRODUCTS_KEY, None)
    configuration.set(shop, SAMPLE_CATEGORIES_KEY, None)
    configuration.set(shop, SAMPLE_CMS_PAGES_KEY, None)


def save_cms_pages(shop, cms_pages_ids):
    """ Save a list of identifiers as a list of sample cms pages for a shop """
    configuration.set(shop, SAMPLE_CMS_PAGES_KEY, cms_pages_ids)


def save_products(shop, products_pk):
    """ Save a list of PK as a list of sample products for a shop """
    configuration.set(shop, SAMPLE_PRODUCTS_KEY, products_pk)


def save_categories(shop, categories_pk):
    """ Save a list of PK as a list of sample categories for a shop """
    configuration.set(shop, SAMPLE_CATEGORIES_KEY, categories_pk)


def has_installed_samples(shop):
    """ Returns whether there is some sample data installed """
    return bool(
        get_installed_products(shop) or get_installed_categories(shop) or get_installed_cms_pages(shop)
    )
