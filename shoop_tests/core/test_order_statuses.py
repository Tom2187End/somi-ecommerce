# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import get_language
import pytest
from shoop.core.models import OrderStatus
from shoop.core.models.orders import OrderStatusRole
from shoop.testing.factories import create_default_order_statuses


@pytest.mark.django_db
def test_order_statuses_are_translatable():
    create_default_order_statuses()
    assert OrderStatus.objects.translated(get_language()).count() == OrderStatus.objects.count()


@pytest.mark.django_db
def test_single_default_status_for_role():
    create_default_order_statuses()
    new_default_cancel = OrderStatus.objects.create(
        identifier="foo",
        role=OrderStatusRole.CANCELED,
        name="foo",
        default=True
    )
    assert new_default_cancel.default
    assert OrderStatus.objects.get_default_canceled() == new_default_cancel
    new_default_cancel.delete()

    # We can use this weird moment to cover the "no default" case, yay
    with pytest.raises(ObjectDoesNotExist):
        OrderStatus.objects.get_default_canceled()

    old_cancel = OrderStatus.objects.get(identifier="canc")
    assert not old_cancel.default  # This will have been reset when another status became the default
    old_cancel.default = True
    old_cancel.save()
