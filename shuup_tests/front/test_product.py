# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.urlresolvers import reverse

from shuup.testing.factories import create_product, get_default_product, get_default_shop


@pytest.mark.django_db
def test_product_page(client):
    get_default_shop()
    product = get_default_product()
    response = client.get(
        reverse('shuup:product', kwargs={
            'pk': product.pk,
            'slug': product.slug
            }
        )
    )
    assert b'no such element' not in response.content, 'All items are not rendered correctly'
    # TODO test purchase_multiple and  sales_unit.allow_fractions


@pytest.mark.django_db
def test_package_product_page(client):
    shop = get_default_shop()
    parent = create_product("test-sku-1", shop=shop)
    child = create_product("test-sku-2", shop=shop)
    parent.make_package({child: 2})
    assert parent.is_package_parent()

    response = client.get(
        reverse('shuup:product', kwargs={
            'pk': parent.pk,
            'slug': parent.slug
            }
        )
    )
    assert b'no such element' not in response.content, 'All items are not rendered correctly'
