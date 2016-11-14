# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime
from decimal import Decimal

import pytest
from django.utils.timezone import make_aware, utc

from shuup.admin.modules.products.forms import ProductAttributesForm
from shuup.core.models import ProductAttribute
from shuup.testing.factories import create_product, get_default_shop
from shuup.utils.objects import compare_partial_dicts
from shuup_tests.utils.forms import get_form_data

VOGONY_DATE = datetime.date(1979, 10, 12)


@pytest.mark.django_db
def test_product_attributes_form():
    # Come up with a decent product...
    product = create_product("TestProduct", shop=get_default_shop())
    assert product.type.attributes.count()
    product.set_attribute_value("bogomips", 6400)
    product.set_attribute_value("genre", "Kauhu", "fi")
    product.set_attribute_value("genre", "Horror", "en")
    product.set_attribute_value("time_to_finish", 12.05)
    product.set_attribute_value("release_date", VOGONY_DATE)
    assert product.get_attribute_value("bogomips") == 6400

    # English is missing on purpose from the languages list; it'll still be available
    # for `genre` as it has an extant value.
    paf = ProductAttributesForm(product=product, languages=("fi", "sv"), default_language="sv")
    assert paf.languages[0] == "sv"

    assert compare_partial_dicts(paf.initial, {  # Check that things get loaded.
        "bogomips": 6400,
        "genre__fi": "Kauhu",
        "genre__en": "Horror",
        "release_date": VOGONY_DATE,
        "time_to_finish": Decimal("12.05")
    })
    form_data = get_form_data(paf)
    form_data.update({  # Change, clear and add fields
        "genre__sv": "Skräck",
        "genre__en": "Terror",
        "bogomips": "",
        "release_date": "",
        "awesome": "True",
        "important_datetime": make_aware(datetime.datetime(2000, 1, 1, 1, 2, 3), utc)
    })
    paf = ProductAttributesForm(product=product, languages=("fi", "sv"), default_language="sv", data=form_data)
    paf.full_clean()
    assert not paf.errors
    paf.save()

    for identifier in ("bogomips", "release_date"):
        # Value should be gone
        assert not product.get_attribute_value(identifier)
        # ... and so should the actual product attribute object
        assert not ProductAttribute.objects.filter(attribute__identifier=identifier, product=product).exists()

    # Those other values got updated, right?
    assert product.get_attribute_value("genre", "en") == form_data["genre__en"]
    assert product.get_attribute_value("genre", "sv") == form_data["genre__sv"]
    assert product.get_attribute_value("awesome") is True
    assert str(product.get_attribute_value("important_datetime")) == "2000-01-01 01:02:03+00:00"
