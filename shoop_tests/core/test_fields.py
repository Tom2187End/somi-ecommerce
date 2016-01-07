# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ImproperlyConfigured

from shoop.core.fields import MeasurementField


def test_measurement_field_doesnt_know_bananas():
    with pytest.raises(ImproperlyConfigured):
        scale = MeasurementField(unit="banana")
