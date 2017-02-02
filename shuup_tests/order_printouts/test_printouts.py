# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.apps.provides import override_provides
from shuup.order_printouts.utils import PrintoutDeliveryExtraInformation
from shuup.order_printouts.admin_module.views import (
    get_confirmation_pdf, get_delivery_pdf, get_delivery_html
)
from shuup.testing.factories import (
    create_order_with_product, create_product, get_default_shop, get_default_supplier
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.importing import load


class TestPrintoutDeliveryExtraFields(PrintoutDeliveryExtraInformation):

    @property
    def extra_fields(self):
        return {
            "Phone": "123456789",
            "Random": "row"
        }


@pytest.mark.django_db
def test_printouts(rf):
    try:
        import weasyprint
    except ImportError:
        pytest.skip()

    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("simple-test-product", shop)
    order = create_order_with_product(product, supplier, 6, 6, shop=shop)
    shipment = order.create_shipment_of_all_products(supplier)
    request = rf.get("/")
    response = get_delivery_pdf(request, shipment.id)
    assert response.status_code == 200
    response = get_confirmation_pdf(request, order.id)
    assert response.status_code == 200


@pytest.mark.django_db
def test_adding_extra_fields_to_the_delivery(rf):
    try:
        import weasyprint
    except ImportError:
        pytest.skip()

    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("simple-test-product", shop)
    order = create_order_with_product(product, supplier, 6, 6, shop=shop)
    shipment = order.create_shipment_of_all_products(supplier)
    request = rf.get("/")

    with override_provides("order_printouts_delivery_extra_fields", [
        "shuup_tests.order_printouts.test_printouts:TestPrintoutDeliveryExtraFields",
    ]):
        response = get_delivery_html(request, shipment.id)
        assert response.status_code == 200
        assert "123456789" in response.content.decode()
        assert "Random" in response.content.decode()
