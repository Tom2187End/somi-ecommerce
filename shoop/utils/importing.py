# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import importlib

_LOAD_CACHE = {}


def load(specification, context_explanation="Load"):
    delimiter = (":" if ":" in specification else ".")
    module_name, object_name = specification.rsplit(delimiter, 1)
    try:
        module = importlib.import_module(module_name)
    except ImportError as ie:  # pragma: no cover
        raise ImproperlyConfigured(
            "%s: Could not import module %r to load %r from. (%r)" % (
                context_explanation, module_name, object_name, ie))

    obj = getattr(module, object_name, None)
    if obj is None:  # pragma: no cover
        raise ImproperlyConfigured(
            "%s: Module %r does not have a name %r, or its value is None." % (
                context_explanation, module, object_name))
    return obj


def clear_load_cache():
    _LOAD_CACHE.clear()


def cached_load(setting_name, default_value=None):
    if setting_name in _LOAD_CACHE:
        return _LOAD_CACHE[setting_name]
    setting_value = getattr(settings, setting_name, None)
    if setting_value is not None:
        value = load(setting_value)
    else:
        value = default_value
    _LOAD_CACHE[setting_name] = value
    return value
