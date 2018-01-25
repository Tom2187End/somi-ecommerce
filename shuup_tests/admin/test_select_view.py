# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import json

import pytest
from django.utils.translation import activate, get_language

from shuup.admin.views.select import MultiselectAjaxView
from shuup.core.models import (
    Category, CompanyContact, PersonContact, Product, ProductMode
)
from shuup.testing.factories import create_product, get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils.fixtures import regular_user


def _get_search_results(rf, view, model_name, search_str, user, search_mode=None):
    data = {
        "model": model_name,
        "search": search_str
    }
    if search_mode:
        data.update({"searchMode": search_mode})

    request = apply_request_middleware(rf.get("sa/search", data), user=user)
    response = view(request)
    assert response.status_code == 200
    return json.loads(response.content.decode("utf-8")).get("results")


@pytest.mark.django_db
def test_ajax_select_view_with_products(rf, admin_user):
    shop = get_default_shop()
    activate("en")
    view = MultiselectAjaxView.as_view()

    # No products, no results
    results = _get_search_results(rf, view, "shuup.Product", "some str", admin_user)
    assert len(results) == 0

    product_name_en = "The Product"
    product = create_product("the product", shop=shop, **{"name": product_name_en})

    product_name_fi = "tuote"
    product.set_current_language("fi")
    # Making sure we are not getting duplicates from translations
    product.name = product_name_fi  # It seems that finnish translation overlaps with english name
    product.save()

    view = MultiselectAjaxView.as_view()

    results = _get_search_results(rf, view, "shuup.Product", "some str", admin_user)
    assert len(results) == 0

    results = _get_search_results(rf, view, "shuup.Product", None, admin_user)
    assert len(results) == 0

    results = _get_search_results(rf, view, "shuup.Product", "product", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == product.id
    assert results[0].get("name") == product_name_en

    activate("fi")
    results = _get_search_results(rf, view, "shuup.Product", "product", admin_user)
    assert get_language() == 'fi'
    assert len(results) == 1
    assert results[0].get("id") == product.id
    assert results[0].get("name") == product_name_fi

    results = _get_search_results(rf, view, "shuup.Product", "  product  ", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == product.id
    assert results[0].get("name") == product_name_fi

    product.soft_delete()
    results = _get_search_results(rf, view, "shuup.Product", "product", admin_user)
    assert len(results) == 0


@pytest.mark.django_db
def test_multi_select_with_main_products(rf, admin_user):
    shop = get_default_shop()
    activate("en")
    view = MultiselectAjaxView.as_view()

    var1 = "size"
    var2 = "color"
    parent = create_product("test", shop=shop, **{"name": "test"})
    for a in range(4):
        for b in range(3):
            product_name = "test-%s-%s" % (a, b)
            child = create_product(product_name, shop=shop, **{"name": product_name})
            child.link_to_parent(parent, variables={var1: a, var2: b})
            assert child.mode == ProductMode.VARIATION_CHILD

    assert parent.variation_children.count() == 4 * 3
    assert Product.objects.count() == 4*3 + 1

    results = _get_search_results(rf, view, "shuup.Product", "test", admin_user)
    assert len(results) == Product.objects.count()

    results = _get_search_results(rf, view, "shuup.Product", "test", admin_user, "main")
    assert len(results) == 1

    create_product("test1", shop=shop, **{"name": "test 123"})
    results = _get_search_results(rf, view, "shuup.Product", "test", admin_user, "main")
    assert len(results) == 2

    create_product("2", shop=shop, **{"name": "something that doesn not match with the search term"})
    results = _get_search_results(rf, view, "shuup.Product", "test", admin_user, "main")
    assert len(results) == 2


@pytest.mark.django_db
@pytest.mark.parametrize("contact_cls", [
    PersonContact, CompanyContact
])
def test_ajax_select_view_with_contacts(rf, contact_cls, admin_user):
    shop = get_default_shop()
    view = MultiselectAjaxView.as_view()
    model_name = "shuup.%s" % contact_cls._meta.model_name
    results = _get_search_results(rf, view, model_name, "some str", admin_user)
    assert len(results) == 0

    customer = contact_cls.objects.create(name="Michael Jackson", email="michael@example.com")
    results = _get_search_results(rf, view, model_name, "michael", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == customer.id
    assert results[0].get("name") == customer.name

    results = _get_search_results(rf, view, model_name, "jacks", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == customer.id
    assert results[0].get("name") == customer.name

    results = _get_search_results(rf, view, model_name, "el@ex", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == customer.id
    assert results[0].get("name") == customer.name

    results = _get_search_results(rf, view, model_name, "random", admin_user)  # Shouldn't find anything with this
    assert len(results) == 0


@pytest.mark.django_db
def test_ajax_select_view_with_categories(rf, admin_user):
    activate("en")
    shop = get_default_shop()
    view = MultiselectAjaxView.as_view()

    # No categories, no results
    results = _get_search_results(rf, view, "shuup.Category", "some str", admin_user)
    assert len(results) == 0

    category = Category.objects.create(
        parent=None,
        identifier="test",
        name="test",
    )
    category.shops.add(shop)

    results = _get_search_results(rf, view, "shuup.Category", "some str", admin_user)
    assert len(results) == 0

    results = _get_search_results(rf, view, "shuup.Category", category.name, admin_user)
    assert len(results) == 1

    category.soft_delete()
    results = _get_search_results(rf, view, "shuup.Category", category.name, admin_user)
    assert len(results) == 0


@pytest.mark.django_db
def test_multiselect_inactive_users_and_contacts(rf, regular_user, admin_user):
    """
    Make sure inactive users and contacts are filtered from search results.
    """
    shop = get_default_shop()
    view = MultiselectAjaxView.as_view()
    assert "joe" in regular_user.username

    results = _get_search_results(rf, view, "auth.User", "joe", admin_user)
    assert len(results) == 1
    assert results[0].get("id") == regular_user.id
    assert results[0].get("name") == regular_user.username

    contact = PersonContact.objects.create(first_name="Joe", last_name="Somebody")

    results = _get_search_results(rf, view, "shuup.PersonContact", "joe", admin_user)

    assert len(results) == 1
    assert results[0].get("id") == contact.id
    assert results[0].get("name") == contact.name

    contact.is_active = False
    contact.save()

    results = _get_search_results(rf, view, "shuup.PersonContact", "joe", admin_user)

    assert len(results) == 0
