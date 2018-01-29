# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import PermissionDenied
from django.test import override_settings
from django.utils.translation import activate

from shuup.admin.shop_provider import (
    AdminShopProvider, get_shop, set_shop, unset_shop
)
from shuup.core.models import Shop, ShopStatus
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
@pytest.mark.parametrize("get_shop_fn", [get_shop, AdminShopProvider().get_shop])
def test_get_shop(rf, get_shop_fn):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        activate("en")
        shop1 = Shop.objects.create(identifier="shop1", status=ShopStatus.ENABLED)
        shop2 = Shop.objects.create(identifier="shop2", status=ShopStatus.ENABLED)

        normal_user = factories.create_random_user()
        staff_user = factories.create_random_user(is_staff=True)

        request = apply_request_middleware(rf.post("/"), user=normal_user)
        # user not staff
        assert get_shop_fn(request) is None

        # staff user now
        request = apply_request_middleware(rf.post("/"), user=staff_user)

        # no shop set
        assert get_shop_fn(request) is None

        # adds the user to a shop
        shop1.staff_members.add(staff_user)
        assert get_shop_fn(request) == shop1

        # adds the user to another shop
        shop2.staff_members.add(staff_user)

        # still the first shop as we do not set any
        assert get_shop_fn(request) == shop1


@pytest.mark.django_db
@pytest.mark.parametrize("set_shop_fn,get_shop_fn", [
    (set_shop, get_shop),
    (AdminShopProvider().set_shop, AdminShopProvider().get_shop)
])
def test_set_shop(rf, set_shop_fn, get_shop_fn):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        activate("en")
        factories.get_default_shop()
        shop1 = Shop.objects.create(identifier="shop1", status=ShopStatus.ENABLED)
        shop2 = Shop.objects.create(identifier="shop2", status=ShopStatus.ENABLED)

        normal_user = factories.create_random_user()
        staff_user = factories.create_random_user(is_staff=True)

        request = apply_request_middleware(rf.post("/"), user=normal_user)
        # user not staff
        with pytest.raises(PermissionDenied):
            set_shop_fn(request, shop1)

        # staff user now
        request = apply_request_middleware(rf.post("/"), user=staff_user)

        # the user is not member of the shop staff
        with pytest.raises(PermissionDenied):
            set_shop_fn(request, shop1)

        assert get_shop_fn(request) is None

        # user is member of the shop staff
        shop1.staff_members.add(staff_user)

        set_shop_fn(request, shop1)
        assert get_shop_fn(request) == shop1

        # can't set a shop which user is not member
        with pytest.raises(PermissionDenied):
            set_shop_fn(request, shop2)

        assert get_shop_fn(request) == shop1

        # adds the user to another shop
        shop2.staff_members.add(staff_user)
        set_shop_fn(request, shop2)
        assert get_shop_fn(request) == shop2


@pytest.mark.django_db
@pytest.mark.parametrize("set_shop_fn,get_shop_fn,unset_shop_fn", [
    (set_shop, get_shop, unset_shop),
    (AdminShopProvider().set_shop, AdminShopProvider().get_shop, AdminShopProvider().unset_shop)
])
def test_unset_shop(rf, set_shop_fn, get_shop_fn, unset_shop_fn):
    activate("en")
    factories.get_default_shop()

    staff_user = factories.create_random_user(is_staff=True)

    shop1 = Shop.objects.create(identifier="shop1", status=ShopStatus.ENABLED)
    shop2 = Shop.objects.create(identifier="shop2", status=ShopStatus.ENABLED)
    shop1.staff_members.add(staff_user)
    shop2.staff_members.add(staff_user)

    request = apply_request_middleware(rf.post("/"), user=staff_user)

    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        set_shop_fn(request, shop2)
        assert get_shop_fn(request) == shop2
        unset_shop_fn(request)

        # returns the first available shop
        assert get_shop_fn(request) == shop1
