# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings
from django.utils.translation import get_language

from shuup.core.models import (
    Attribute, AttributeType, AttributeVisibility, Product, ProductAttribute
)
from shuup.core.models._attributes import NoSuchAttributeHere
from shuup.testing.factories import (
    ATTR_SPECS, create_product, get_default_attribute_set, get_default_product
)


def _populate_applied_attribute(aa):
    if aa.attribute.type == AttributeType.BOOLEAN:
        aa.value = True
        aa.save()
        assert aa.value is True, "Truth works"
        assert aa.untranslated_string_value == "1", "Integer attributes save string representations"
        aa.value = not 42  # (but it could be something else)
        aa.save()
        assert aa.value is False, "Lies work"
        assert aa.untranslated_string_value == "0", "Integer attributes save string representations"
        return

    if aa.attribute.type == AttributeType.INTEGER:
        aa.value = 320.51
        aa.save()
        assert aa.value == 320, "Integer attributes get rounded down"
        assert aa.untranslated_string_value == "320", "Integer attributes save string representations"
        return

    if aa.attribute.type == AttributeType.DECIMAL:
        aa.value = Decimal("0.636")  # Surface pressure of Mars
        aa.save()
        assert aa.value * 1000 == 636, "Decimals work like they should"
        assert aa.untranslated_string_value == "0.636", "Decimal attributes save string representations"
        return

    if aa.attribute.type == AttributeType.TIMEDELTA:
        aa.value = 86400
        aa.save()
        assert aa.value.days == 1, "86,400 seconds is one day"
        assert aa.untranslated_string_value == "86400", "Timedeltas are seconds as strings"

        aa.value = datetime.timedelta(days=4)
        aa.save()
        assert aa.value.days == 4, "4 days remain as 4 days"
        assert aa.untranslated_string_value == "345600", "Timedeltas are still seconds as strings"
        return

    if aa.attribute.type == AttributeType.UNTRANSLATED_STRING:
        aa.value = "Dog Hello"
        aa.save()
        assert aa.value == "Dog Hello", "Untranslated strings work"
        assert aa.untranslated_string_value == "Dog Hello", "Untranslated strings work"
        return

    if aa.attribute.type == AttributeType.TRANSLATED_STRING:
        assert aa.attribute.is_translated
        with override_settings(LANGUAGES=[(x, x) for x in ("en", "fi", "ga", "ja")]):
            versions = {
                "en": u"science fiction",
                "fi": u"tieteiskirjallisuus",
                "ga": u"ficsean eolaíochta",
                "ja": u"空想科学小説",
            }
            for language_code, text in versions.items():
                aa.set_current_language(language_code)
                aa.value = text
                aa.save()
                assert aa.value == text, "Translated strings work"
            for language_code, text in versions.items():
                assert aa.safe_translation_getter("translated_string_value", language_code=language_code) == text, "%s translation is safe" % language_code

            aa.set_current_language("xx")
            assert aa.value == "", "untranslated version yields an empty string"

        return

    if aa.attribute.type == AttributeType.DATE:
        aa.value = "2014-01-01"
        assert aa.value == datetime.date(2014, 1, 1), "Date parsing works"
        assert aa.untranslated_string_value == "2014-01-01", "Dates are saved as strings"
        return

    if aa.attribute.type == AttributeType.DATETIME:
        with pytest.raises(TypeError):
            aa.value = "yesterday"
        dt = datetime.datetime(1997, 8, 12, 14)
        aa.value = dt
        assert aa.value.toordinal() == 729248, "Date assignment works"
        assert aa.value.time().hour == 14, "The clock still works"
        assert aa.untranslated_string_value == dt.isoformat(), "Datetimes are saved as strings too"
        return

    raise NotImplementedError("Not implemented: populating %s" % aa.attribute.type)  # pragma: no cover


@pytest.mark.django_db
def test_applied_attributes():
    product = get_default_product()
    for spec in ATTR_SPECS:  # This loop sets each attribute twice. That's okay.
        attr = Attribute.objects.get(identifier=spec["identifier"])
        pa, _ = ProductAttribute.objects.get_or_create(product=product, attribute=attr)
        _populate_applied_attribute(pa)
        pa.save()
        if not attr.is_translated:
            product.set_attribute_value(attr.identifier, pa.value)

    assert product.get_attribute_value("bogomips") == 320, "integer attribute loaded neatly"
    product.set_attribute_value("bogomips", 480)
    assert product.get_attribute_value("bogomips") == 480, "integer attribute updated neatly"
    Product.cache_attributes_for_targets(
        applied_attr_cls=ProductAttribute,
        targets=[product],
        attribute_identifiers=[a["identifier"] for a in ATTR_SPECS],
        language=get_language()
    )
    assert (get_language(), "bogomips",) in product._attr_cache, "integer attribute in cache"
    assert product.get_attribute_value("bogomips") == 480, "integer attribute value in cache"
    assert product.get_attribute_value("ba:gelmips", default="Britta") == "Britta", "non-existent attributes return default value"
    assert product._attr_cache[(get_language(), "ba:gelmips")] is NoSuchAttributeHere, "cache miss saved"
    attr_info = product.get_all_attribute_info(language=get_language(), visibility_mode=AttributeVisibility.SHOW_ON_PRODUCT_PAGE)
    assert set(attr_info.keys()) <= set(a["identifier"] for a in ATTR_SPECS), "get_all_attribute_info gets all attribute info"


@pytest.mark.django_db
def test_get_set_attribute():
    product = create_product("ATTR_TEST")
    product.set_attribute_value("awesome", True)
    product.set_attribute_value("bogomips", 10000)
    product.set_attribute_value("bogomips", None)
    product.set_attribute_value("author", None)
    product.set_attribute_value("genre", "Kenre", "fi")

    with pytest.raises(ValueError):
        product.set_attribute_value("genre", "Kenre")

    with pytest.raises(ObjectDoesNotExist):
        product.set_attribute_value("keppi", "stick")



def test_saving_invalid_attribute():
    with pytest.raises(ValueError):
        Attribute(identifier=None).save()
