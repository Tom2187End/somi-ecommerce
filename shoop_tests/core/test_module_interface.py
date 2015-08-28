# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
import pytest

from shoop.core.models import Supplier


@pytest.mark.django_db
def test_module_interface_for_scandinavian_letters(rf):
    supplier = Supplier.objects.create(identifier="module_interface_test", name="ääääööööååå")

    assert isinstance(supplier, Supplier)
    assert supplier.module
    assert "%r" % supplier

    supplier.delete()
