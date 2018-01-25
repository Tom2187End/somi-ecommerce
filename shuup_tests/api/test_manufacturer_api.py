# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import Manufacturer
from shuup.testing.factories import get_default_shop, create_product


def setup_function(fn):
    cache.clear()


def test_manufacturer_api(admin_user):
    get_default_shop()
    client = APIClient()
    client.force_authenticate(user=admin_user)

    manufacturer_data = {
        "name": "manu 1",
        "url": "http://www.google.com"
    }
    response = client.post("/api/shuup/manufacturer/",
                           content_type="application/json",
                           data=json.dumps(manufacturer_data))
    assert response.status_code == status.HTTP_201_CREATED
    manufacturer = Manufacturer.objects.first()
    assert manufacturer.name == manufacturer_data["name"]
    assert manufacturer.url == manufacturer_data["url"]

    manufacturer_data["name"] = "name 2"
    manufacturer_data["url"] = "http://yahoo.com"

    response = client.put("/api/shuup/manufacturer/%d/" % manufacturer.id,
                          content_type="application/json",
                          data=json.dumps(manufacturer_data))
    assert response.status_code == status.HTTP_200_OK
    manufacturer = Manufacturer.objects.first()
    assert manufacturer.name == manufacturer_data["name"]
    assert manufacturer.url == manufacturer_data["url"]

    response = client.get("/api/shuup/manufacturer/%d/" % manufacturer.id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert manufacturer.name == data["name"]
    assert manufacturer.url == data["url"]

    response = client.get("/api/shuup/manufacturer/")
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert manufacturer.name == data[0]["name"]
    assert manufacturer.url == data[0]["url"]

    response = client.delete("/api/shuup/manufacturer/%d/" % manufacturer.id)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Manufacturer.objects.count() == 0

    # create a product and relate it to a manufacturer
    product = create_product("product with manufacturer")
    manufacturer = Manufacturer.objects.create()
    product.manufacturer = manufacturer
    product.save()

    # shouldn't be possible to delete a manufacturer with a related product
    response = client.delete("/api/shuup/manufacturer/%d/" % manufacturer.id)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "This object can not be deleted because it is referenced by" in response.content.decode("utf-8")
    assert Manufacturer.objects.count() == 1
