# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import babel
import babel.numbers
from babel.numbers import format_currency
from django.utils import translation
from django.utils.lru_cache import lru_cache


@lru_cache()
def get_babel_locale(locale_string):
    """
    Parse a Django-format (dash-separated) locale string
    and return a Babel locale.

    This function is decorated with lru_cache, so executions
    should be cheap even if `babel.Locale.parse()` most definitely
    is not.

    :param locale_string: A locale string ("en-US", "fi-FI", "fi")
    :type locale_string: str
    :return: Babel Locale
    :rtype: babel.Locale
    """
    return babel.Locale.parse(locale_string, "-")


def get_current_babel_locale(fallback="en-US-POSIX"):
    """
    Get a Babel locale based on the thread's locale context.

    :param fallback:
      Locale to fallback to; set to None to raise an exception instead.
    :return: Babel Locale
    :rtype: babel.Locale
    """
    locale = get_babel_locale(locale_string=translation.get_language())
    if not locale:
        if fallback:
            locale = get_babel_locale(fallback)
        if not locale:
            raise ValueError(
                "Failed to get current babel locale (lang=%s)" %
                (translation.get_language(),))
    return locale


def format_percent(value, digits=0):
    locale = get_current_babel_locale()
    pattern = locale.percent_formats.get(None).pattern
    new_pattern = pattern.replace("0", "0." + (digits * "0"))
    return babel.numbers.format_percent(value, new_pattern, locale)


def format_money(amount, digits=None, widen=0, locale=None):
    loc = babel.Locale.parse(locale or get_current_babel_locale())

    pattern = loc.currency_formats.get(None).pattern

    # pattern is a formatting string.  Couple examples:
    # '¤#,##0.00', '#,##0.00\xa0¤', '\u200e¤#,##0.00', and '¤#0.00'

    if digits is not None:
        pattern = pattern.replace(".00", "." + (digits * "0"))
    if widen:
        pattern = pattern.replace(".00", ".00" + (widen * "0"))
    return format_currency(amount.value, amount.currency, pattern, loc)


def get_language_name(language_code):
    return get_current_babel_locale().languages.get(language_code, language_code)
