# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.utils.functional import lazy
from shoop.notify.base import Condition, Binding, ConstantUse
from shoop.notify.typology import Language, Text, Integer, Boolean
from shoop.utils.text import camel_case
import six
from django.utils.translation import ugettext_lazy as _


class NonEmpty(Condition):
    identifier = "non_empty"
    description = _(u"Check whether the bound value `value` exists and is non-empty and non-zero.")
    name = _("Non-Empty")
    v = Binding("Value")

    def test(self, context):
        return bool(self.get_value(context, "v"))


class Empty(Condition):
    identifier = "empty"
    description = _(u"Check whether the bound value `value` is empty or zero.")
    name = _("Empty")
    v = Binding("Value")

    def test(self, context):
        return not bool(self.get_value(context, "v"))


class BaseEqual(Condition):
    identifier_suffix = "equal"

    def test(self, context):
        value1 = self.get_value(context, "v1")
        value2 = self.get_value(context, "v2")

        if isinstance(value1, six.text_type) or isinstance(value2, six.text_type):
            # When either value is a string, compare them stringly typed.
            # (see http://c2.com/cgi/wiki?StringlyTyped)
            return six.text_type(value1) == six.text_type(value2)

        return value1 == value2


class CaseInsensitiveStringEqual(Condition):
    identifier_suffix = "equal"

    def test(self, context):
        value1 = self.get_value(context, "v1")
        value2 = self.get_value(context, "v2")
        value1 = six.text_type(value1).lower().strip()
        value2 = six.text_type(value2).lower().strip()
        return (value1 == value2)


def construct_simple(base, var_type):
    identifier = "%s_%s" % (var_type.identifier, base.identifier_suffix)
    class_name = str(camel_case(identifier))
    suffixed_type_name = lazy(lambda s: "%s %s" % (var_type.name, s), six.text_type)
    class_ns = {
        "bindings": {
            "v1": Binding(suffixed_type_name("1"), type=var_type),
            "v2": Binding(suffixed_type_name("2"), type=var_type, constant_use=ConstantUse.VARIABLE_OR_CONSTANT),
        },
        "identifier": identifier
    }
    return type(class_name, (base,), class_ns)


LanguageEqual = construct_simple(CaseInsensitiveStringEqual, Language)
TextEqual = construct_simple(CaseInsensitiveStringEqual, Text)
IntegerEqual = construct_simple(BaseEqual, Integer)
BooleanEqual = construct_simple(BaseEqual, Boolean)
