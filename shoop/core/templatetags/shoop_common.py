# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from datetime import date
from json import dumps as json_dump

from babel.dates import format_date, format_datetime, format_time
from babel.numbers import format_decimal, format_percent
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime
from django_jinja import library
from jinja2.runtime import Undefined

from shoop.utils.i18n import format_home_currency, get_current_babel_locale
from shoop.utils.serialization import ExtendedJSONEncoder


@library.filter
def home_currency(value):
    return format_home_currency(value, locale=get_current_babel_locale())


@library.filter
def percent(value, ndigits=3):
    locale = get_current_babel_locale()
    if not ndigits:
        return format_percent(value, locale=locale)
    else:
        format = locale.percent_formats.get(None)
        new_fmt = format.pattern.replace("0", "0." + (ndigits * "#"))
        return format_percent(value, format=new_fmt, locale=locale)


@library.filter
def number(value):
    return format_decimal(value, locale=get_current_babel_locale())


@library.filter
def datetime(value, kind="datetime", format="medium", tz=True):
    """
    Format a datetime for human consumption.

    The currently active locale's formatting rules are used.  The output
    of this function is probably not machine-parseable.

    :param value: datetime object to format
    :type value: datetime.datetime

    :param kind: Format as 'datetime', 'date' or 'time'
    :type kind: str

    :param format:
      Format specifier or one of 'full', 'long', 'medium' or 'short'
    :type format: str

    :param tz:
      Convert to current or given timezone. Accepted values are:

         True (default)
             convert to currently active timezone (as reported by
             :func:`django.utils.timezone.get_current_timezone`)
         False (or other false value like empty string)
             do no convert to any timezone (use UTC)
         Other values (as str)
             convert to given timezone (e.g. ``"US/Hawaii"``)
    :type tz: bool|str
    """

    locale = get_current_babel_locale()

    if type(value) is date:  # Not using isinstance, since `datetime`s are `date` too.
        # We can't do any TZ manipulation for dates, so just use `format_date` always
        return format_date(value, format=format, locale=locale)

    if tz:
        value = localtime(value, (None if tz is True else tz))

    if kind == "datetime":
        return format_datetime(value, format=format, locale=locale)
    elif kind == "date":
        return format_date(value, format=format, locale=locale)
    elif kind == "time":
        return format_time(value, format=format, locale=locale)
    else:
        raise ValueError("Unknown `datetime` kind: %r" % kind)


@library.filter(name="json")
def json(value):
    if isinstance(value, Undefined):
        value = None
    return mark_safe(json_dump(value, cls=ExtendedJSONEncoder))
