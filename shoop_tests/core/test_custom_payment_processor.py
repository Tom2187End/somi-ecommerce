# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from decimal import Decimal

import pytest

from shoop.core.models import (
    CustomPaymentProcessor, PaymentMethod, PaymentStatus, PaymentUrls
)
from shoop.core.pricing import TaxfulPrice
from shoop.testing.factories import (
    create_order_with_product, get_default_product, get_default_shop,
    get_default_supplier, get_default_tax_class
)


@pytest.mark.django_db
@pytest.mark.parametrize('choice_identifier, expected_payment_status', [
    ('cash', PaymentStatus.FULLY_PAID),
    ('manual', PaymentStatus.DEFERRED)
])
def test_custom_payment_processor_cash_service(choice_identifier, expected_payment_status):
    shop = get_default_shop()
    product = get_default_product()
    supplier = get_default_supplier()
    processor = CustomPaymentProcessor.objects.create()
    payment_method = PaymentMethod.objects.create(
        shop=shop,
        payment_processor=processor,
        choice_identifier=choice_identifier,
        tax_class=get_default_tax_class())
    order = create_order_with_product(
        product=product,
        supplier=supplier,
        quantity=1,
        taxless_base_unit_price=Decimal('5.55'),
        shop=shop)
    order.taxful_total_price = TaxfulPrice(Decimal('5.55'), u'EUR')
    order.payment_method = payment_method
    order.save()

    assert order.payment_status == PaymentStatus.NOT_PAID
    processor.process_payment_return_request(choice_identifier, order, None)
    assert order.payment_status == expected_payment_status
    processor.process_payment_return_request(choice_identifier, order, None)
    assert order.payment_status == expected_payment_status
