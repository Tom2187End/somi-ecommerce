# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import re
from decimal import Decimal

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.forms import Form, ModelForm
from django.forms.widgets import NumberInput
from django.utils.encoding import force_text

from shuup.core.fields import FormattedDecimalFormField, MeasurementField
from shuup.core.models import Product


def test_measurement_field_doesnt_know_bananas():
    with pytest.raises(ImproperlyConfigured):
        scale = MeasurementField(unit="banana")


def test_formatted_decimal_field():
    """
    Test that FormattedDecimalField doesn't return value in scientific
    notation.
    """

    class TestModelForm(ModelForm):
        class Meta:
            model = Product
            fields = ["width"]

    values = [
        "0E-9", "0E-30", "1E-9", "123E-10", "-123E-10", "1.12345666666666E20"
    ]

    for value in values:
        product = Product(width=Decimal(value))
        form = TestModelForm(instance=product)
        rendered_form = force_text(form)
        rendered_value = re.search('value="(.*?)"', rendered_form).group(1)
        rendered_step = re.search('step="(.*?)"', rendered_form).group(1)
        assert rendered_value and "E" not in rendered_value
        assert rendered_step and "E" not in rendered_step

    # Extremely large exponents should raise an exception so as not to
    # produce excessively large files
    large_value = "1.23E-10000"
    product = Product(width=Decimal(large_value))
    with pytest.raises(ValueError):
        form = TestModelForm(instance=product)


@pytest.mark.parametrize("decimal_places, expected_step", [
    (2, '0.01'),
    (3, '0.001'),
    (0, '1'),
    (6, 'any')
])
def test_formatted_decimal_field_step(decimal_places, expected_step):
    field = FormattedDecimalFormField(max_digits=10, decimal_places=decimal_places)

    class TestForm(Form):
        f = field

    rendered_field = force_text(TestForm()['f'])
    rendered_step = re.search('step="(.*?)"', rendered_field).group(1)
    assert rendered_step == expected_step


def test_formatted_decimal_field_overridden_step():
    field = FormattedDecimalFormField(max_digits=10, decimal_places=10, widget=NumberInput(attrs={'step': '0.1'}))

    class TestForm(Form):
        f = field

    rendered_field = force_text(TestForm()['f'])
    rendered_step = re.search('step="(.*?)"', rendered_field).group(1)
    assert rendered_step == '0.1'


def test_formatted_decimal_field_default():
    class TestModelForm(ModelForm):
        class Meta:
            model = Product
            fields = ["width"]

    rendered_form = force_text(TestModelForm(instance=Product()))
    rendered_value = re.search('value="(.*?)"', rendered_form).group(1)
    assert rendered_value == "0"
