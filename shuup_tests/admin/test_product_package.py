# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.forms import formset_factory

from shuup.admin.modules.products.forms import (
    PackageChildForm, PackageChildFormSet
)
from shuup.admin.modules.products.utils import clear_existing_package
from shuup.core.models import ProductMode
from shuup.testing.factories import create_product
from shuup.utils.excs import Problem
from shuup_tests.utils import printable_gibberish
from shuup_tests.utils.forms import get_form_data


@pytest.mark.django_db
def test_package_child_formset():
    FormSet = formset_factory(PackageChildForm, PackageChildFormSet, extra=5, can_delete=True)
    parent = create_product(printable_gibberish())
    child = create_product(printable_gibberish())

    # No products in the package
    formset = FormSet(parent_product=parent)
    assert formset.initial_form_count() == 0 # No children yet

    assert not parent.get_all_package_children()

    data = dict(get_form_data(formset, True), **{"form-0-child": child.pk, "form-0-quantity": 2})
    formset = FormSet(parent_product=parent, data=data)
    formset.save()
    assert parent.get_all_package_children()

    clear_existing_package(parent)
    assert not parent.get_all_package_children()


@pytest.mark.django_db
def test_product_not_in_normal_mode():
    FormSet = formset_factory(PackageChildForm, PackageChildFormSet, extra=5, can_delete=True)
    parent = create_product(printable_gibberish())
    child_1 = create_product(printable_gibberish())
    child_1.link_to_parent(parent)
    child_2 = create_product(printable_gibberish())
    parent.verify_mode()

    assert parent.mode == ProductMode.SIMPLE_VARIATION_PARENT

    # Trying to create a package from a non-normal mode product
    with pytest.raises(Problem):
        formset = FormSet(parent_product=parent)
        data = dict(get_form_data(formset, True), **{"form-0-child": child_2.pk, "form-0-quantity": 2})
        formset = FormSet(parent_product=parent, data=data)
        formset.save()


@pytest.mark.django_db
def test_cannot_add_product_to_own_package(rf):
    FormSet = formset_factory(PackageChildForm, PackageChildFormSet, extra=5, can_delete=True)
    parent = create_product(printable_gibberish())

    # No products in the package
    formset = FormSet(parent_product=parent)
    assert formset.initial_form_count() == 0 # No children yet

    assert not parent.get_all_package_children()

    # Try to add a product to its own package
    data = dict(get_form_data(formset, True), **{"form-0-child": parent.pk, "form-0-quantity": 2})
    formset = FormSet(parent_product=parent, data=data)
    formset.save()
    assert not parent.get_all_package_children()
