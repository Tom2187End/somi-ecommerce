# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
from django.http.response import Http404
from django.test import override_settings

from shuup.admin.shop_provider import set_shop
from shuup.core.models import Shop
from shuup.discounts.admin.views import CouponCodeDeleteView, CouponCodeEditView, CouponCodeListView
from shuup.discounts.models import CouponCode, Discount
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


def _assert_view_get(rf, instance, shop, user, raises_404=False):
    request = apply_request_middleware(rf.get("/"), user=user, shop=shop)
    set_shop(request, shop)
    view_func = CouponCodeEditView.as_view()
    if raises_404:
        with pytest.raises(Http404):
            view_func(request, pk=instance.pk)
    else:
        response = view_func(request, pk=instance.pk)
        assert response.status_code == 200


@pytest.mark.django_db
def test_coupon_codes_admin_edit_view(rf, staff_user, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        shop = factories.get_default_shop()
        shop.staff_members.add(staff_user)
        factories.get_shop(identifier="shop2", enabled=True)
        assert Shop.objects.count() == 2

        # Staff user gets shop automatically
        data = {"code": "potus"}
        request = apply_request_middleware(rf.post("/", data=data), user=staff_user, shop=shop)
        set_shop(request, shop)
        assert request.shop == shop
        view_func = CouponCodeEditView.as_view()
        response = view_func(request)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == 302
        coupon1 = CouponCode.objects.first()
        assert coupon1.shops.first() == shop

        # Test with superuser and with different shop
        shop2 = factories.get_shop(enabled=True)
        request = apply_request_middleware(rf.post("/", data=data), user=admin_user, shop=shop2)
        set_shop(request, shop2)
        assert request.shop == shop2
        view_func = CouponCodeEditView.as_view()
        response = view_func(request)
        assert response.status_code == 302
        assert CouponCode.objects.count() == 2

        coupon2 = CouponCode.objects.exclude(id=coupon1.pk).first()
        assert coupon1 != coupon2
        assert coupon2.shops.count() == 1
        assert coupon2.shops.filter(id=shop2.pk).exists()

        # Staff user can only view coupon codes for his shop
        _assert_view_get(rf, coupon1, shop, staff_user)
        _assert_view_get(rf, coupon2, shop, staff_user, True)

        # Superuser can see both if needed, but only when right shop is active
        _assert_view_get(rf, coupon1, shop, admin_user)
        _assert_view_get(rf, coupon2, shop, admin_user, True)
        _assert_view_get(rf, coupon2, shop2, admin_user)


@pytest.mark.django_db
def test_coupon_codes_admin_edit_form_set_discount(rf, staff_user, admin_user):
    shop = factories.get_default_shop()
    shop.staff_members.add(staff_user)

    discount = Discount.objects.create()
    data = {"code": "usa"}
    request = apply_request_middleware(rf.post("/", data=data), user=staff_user, shop=shop)
    set_shop(request, shop)
    assert request.shop == shop
    view_func = CouponCodeEditView.as_view()
    response = view_func(request)
    if hasattr(response, "render"):
        response.render()

    assert response.status_code == 302
    coupon1 = CouponCode.objects.first()
    data.update({"coupon_code_discounts": [discount]})
    request = apply_request_middleware(rf.post("/", data=data), user=staff_user, shop=shop)
    view_func = CouponCodeEditView.as_view()
    response = view_func(request, pk=coupon1.pk)
    if hasattr(response, "render"):
        response.render()

    assert response.status_code == 302
    discount = Discount.objects.first()
    assert discount.coupon_code is None  # discount is missing shop so this shouldn't be set

    discount.shops.add(shop)
    request = apply_request_middleware(rf.post("/", data=data), user=staff_user, shop=shop)
    view_func = CouponCodeEditView.as_view()
    response = view_func(request, pk=coupon1.pk)
    if hasattr(response, "render"):
        response.render()

    assert response.status_code == 302
    discount = Discount.objects.first()
    assert discount.coupon_code == coupon1


def _test_coupon_code_list_view(rf, index):
    shop = factories.get_shop(identifier="shop%s" % index, enabled=True)
    staff_user = factories.create_random_user(is_staff=True)
    shop.staff_members.add(staff_user)

    coupon_code = CouponCode.objects.create(code="%s" % index)
    coupon_code.shops.add(shop)

    view_func = CouponCodeListView.as_view()
    request = apply_request_middleware(
        rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=staff_user, shop=shop
    )
    set_shop(request, shop)
    response = view_func(request)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code == 200

    view_instance = CouponCodeListView()
    view_instance.request = request
    assert request.shop == shop
    assert view_instance.get_queryset().count() == 1

    data = json.loads(view_instance.get(request).content.decode("UTF-8"))
    assert len(data["items"]) == 1
    coupon_code_data = [item for item in data["items"] if item["_id"] == coupon_code.pk][0]
    assert coupon_code_data["usages"] == 0


@pytest.mark.django_db
def test_coupon_codes_admin_list_view(rf, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        for x in range(3):
            _test_coupon_code_list_view(rf, x)

        # Superuser gets same data as shop staff
        shop = Shop.objects.exclude(identifier=factories.DEFAULT_IDENTIFIER).order_by("?").first()
        request = apply_request_middleware(
            rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=admin_user, shop=shop
        )
        set_shop(request, shop)
        view_instance = CouponCodeListView()
        view_instance.request = request
        data = json.loads(view_instance.get(request).content.decode("UTF-8"))
        assert len(data["items"]) == 1


def _test_coupon_code_delete_view(rf, index):
    shop = factories.get_shop(identifier="shop%s" % index, enabled=True)
    staff_user = factories.create_random_user(is_staff=True)
    shop.staff_members.add(staff_user)
    code = "code-%s" % index
    coupon = CouponCode.objects.create(code=code)
    coupon.shops.add(shop)
    extra_coupon = CouponCode.objects.create(code="extra-coupon-%s" % index)
    extra_coupon.shops.add(shop)

    assert CouponCode.objects.filter(code=code).exists()
    view_func = CouponCodeDeleteView.as_view()
    request = apply_request_middleware(rf.post("/"), user=staff_user, shop=shop)
    set_shop(request, shop)
    response = view_func(request, pk=coupon.pk)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code == 302
    assert not CouponCode.objects.filter(code=code).exists()

    # Make sure that this staff can't remove other people discounts
    other_coupons = CouponCode.objects.exclude(shops=shop)
    coupon_count = other_coupons.count()
    for coupon in other_coupons:
        view_func = CouponCodeDeleteView.as_view()
        request = apply_request_middleware(rf.post("/"), user=staff_user, shop=shop)
        set_shop(request, shop)
        with pytest.raises(Http404):
            response = view_func(request, pk=coupon.pk)
            if hasattr(response, "render"):
                response.render()

    assert coupon_count == CouponCode.objects.exclude(shops=shop).count()


@pytest.mark.django_db
def test_coupon_codes_admin_delete_view(rf):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        for x in range(3):
            _test_coupon_code_delete_view(rf, x)
