# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal
import numbers

import babel
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import BLANK_CHOICE_DASH
from django.forms.widgets import NumberInput
from django.utils.translation import ugettext_lazy as _
from jsonfield.fields import JSONField

from shuup.core.fields.tagged_json import tag_registry, TaggedJSONEncoder
from shuup.utils.i18n import get_current_babel_locale

IdentifierValidator = RegexValidator("[a-z][a-z_]+")

MONEY_FIELD_DECIMAL_PLACES = 9


class InternalIdentifierField(models.CharField):

    def __init__(self, **kwargs):
        if "unique" not in kwargs:
            raise ValueError("You must explicitly set the `unique` flag for `InternalIdentifierField`s.")
        kwargs.setdefault("max_length", 64)
        kwargs.setdefault("blank", True)
        kwargs.setdefault("null", bool(kwargs.get("blank")))  # If it's allowed to be blank, it should be null
        kwargs.setdefault("verbose_name", _("internal identifier"))
        kwargs.setdefault("help_text", _(u"Do not change this value if you are not sure what you're doing."))
        kwargs.setdefault("editable", False)
        super(InternalIdentifierField, self).__init__(**kwargs)
        self.validators.append(IdentifierValidator)

    def get_prep_value(self, value):
        # Save `None`s instead of falsy values (such as empty strings)
        # for `InternalIdentifierField`s to avoid `IntegrityError`s on unique fields.
        prepared_value = super(InternalIdentifierField, self).get_prep_value(value)
        if self.null:
            return (prepared_value or None)
        return prepared_value

    def deconstruct(self):
        (name, path, args, kwargs) = super(InternalIdentifierField, self).deconstruct()
        kwargs["null"] = self.null
        kwargs["unique"] = self.unique
        kwargs["blank"] = self.blank
        # Irrelevant for migrations, and usually translated anyway:
        kwargs.pop("verbose_name", None)
        kwargs.pop("help_text", None)
        return (name, path, args, kwargs)


class CurrencyField(models.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 4)
        super(CurrencyField, self).__init__(**kwargs)


class FormattedDecimalFormField(forms.DecimalField):
    # Chrome automatically converts a step with more than 5 decimals places to scientific notation
    MAX_DECIMAL_PLACES_FOR_STEP = 5

    def widget_attrs(self, widget):
        # be more lenient when setting step than the default django widget_attrs
        if isinstance(widget, NumberInput) and 'step' not in widget.attrs:
            if self.decimal_places <= self.MAX_DECIMAL_PLACES_FOR_STEP:
                step = format(decimal.Decimal('1') / 10 ** self.decimal_places, 'f')
            else:
                step = 'any'
            widget.attrs.setdefault('step', step)
        return super(FormattedDecimalFormField, self).widget_attrs(widget)


class FormattedDecimalField(models.DecimalField):
    """
    DecimalField subclass to display decimal values in non-scientific
    format.
    """
    def value_from_object(self, obj):
        value = super(FormattedDecimalField, self).value_from_object(obj)
        if isinstance(value, numbers.Number):
            return self.format_decimal(decimal.Decimal(str(value)))

    def format_decimal(self, value, max_digits=100, exponent_limit=100):
        assert isinstance(value, decimal.Decimal)
        val = value.normalize()
        (sign, digits, exponent) = val.as_tuple()
        if exponent > exponent_limit:
            raise ValueError('Exponent too large for formatting: %r' % value)
        elif exponent < -exponent_limit:
            raise ValueError('Exponent too small for formatting: %r' % value)
        if len(digits) > max_digits:
            raise ValueError('Too many digits for formatting: %r' % value)
        return format(val, 'f')

    def formfield(self, **kwargs):
        kwargs.setdefault("form_class", FormattedDecimalFormField)
        return super(FormattedDecimalField, self).formfield(**kwargs)


class MoneyValueField(FormattedDecimalField):
    def __init__(self, **kwargs):
        kwargs.setdefault("decimal_places", MONEY_FIELD_DECIMAL_PLACES)
        kwargs.setdefault("max_digits", 36)
        super(MoneyValueField, self).__init__(**kwargs)


class QuantityField(FormattedDecimalField):
    def __init__(self, **kwargs):
        kwargs.setdefault("decimal_places", 9)
        kwargs.setdefault("max_digits", 36)
        kwargs.setdefault("default", 0)
        super(QuantityField, self).__init__(**kwargs)


class MeasurementField(FormattedDecimalField):
    KNOWN_UNITS = ("mm", "m", "kg", "g", "m3")

    def __init__(self, unit, **kwargs):
        if unit not in self.KNOWN_UNITS:
            raise ImproperlyConfigured("Unit %r is not a known unit." % unit)
        self.unit = unit
        kwargs.setdefault("decimal_places", 9)
        kwargs.setdefault("max_digits", 36)
        kwargs.setdefault("default", 0)
        super(MeasurementField, self).__init__(**kwargs)

    def deconstruct(self):
        parent = super(MeasurementField, self)
        (name, path, args, kwargs) = parent.deconstruct()
        kwargs["unit"] = self.unit
        return (name, path, args, kwargs)


class LanguageField(models.CharField):
    # TODO: This list will include extinct languages
    LANGUAGE_CODES = set(babel.Locale("en").languages.keys())

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 10)
        kwargs["choices"] = [(code, code) for code in sorted(self.LANGUAGE_CODES)]
        super(LanguageField, self).__init__(*args, **kwargs)

    def get_choices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH):
        locale = get_current_babel_locale()
        translated_choices = [
            (code, locale.languages.get(code, code))
            for (code, _)
            in super(LanguageField, self).get_choices(include_blank, blank_choice)
        ]
        translated_choices.sort(key=lambda pair: pair[1].lower())
        return translated_choices


# https://docs.djangoproject.com/en/1.8/ref/models/fields/#django.db.models.ForeignKey.allow_unsaved_instance_assignment
class UnsavedForeignKey(models.ForeignKey):
    allow_unsaved_instance_assignment = True


class TaggedJSONField(JSONField):
    def __init__(self, *args, **kwargs):
        dump_kwargs = kwargs.setdefault("dump_kwargs", {})
        dump_kwargs.setdefault("cls", TaggedJSONEncoder)
        dump_kwargs.setdefault("separators", (',', ':'))
        load_kwargs = kwargs.setdefault("load_kwargs", {})
        load_kwargs.setdefault("object_hook", tag_registry.decode)
        super(TaggedJSONField, self).__init__(*args, **kwargs)
