# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ValidationError
from django.test.utils import override_settings

from shuup.core.basket import commands as basket_commands
from shuup.core.basket import get_basket
from shuup.core.models import AnonymousContact, get_person_contact
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware

CORE_BASKET_SETTINGS = dict(
    SHUUP_BASKET_ORDER_CREATOR_SPEC="shuup.core.basket.order_creator:BasketOrderCreator",
    SHUUP_BASKET_STORAGE_CLASS_SPEC="shuup.core.basket.storage:DatabaseBasketStorage",
    SHUUP_BASKET_CLASS_SPEC="shuup.core.basket.objects:Basket"
)

@pytest.mark.django_db
def test_set_from_customer_to_anonymous(rf):
    """
    Set anonymous to the basket customer
    """
    with override_settings(**CORE_BASKET_SETTINGS):
        user = factories.create_random_user()
        request = apply_request_middleware(rf.get("/"), user=user)
        basket = get_basket(request, "basket")
        basket.customer = get_person_contact(user)
        assert basket_commands.handle_set_customer(request, basket, AnonymousContact())["ok"] is True
        assert basket.customer == AnonymousContact()
        assert basket.orderer == AnonymousContact()
        assert basket.creator == user


@pytest.mark.django_db
def test_set_from_admin_to_anonymous(admin_user, rf):
    """
    Set anonymous to the basket customer
    """
    with override_settings(**CORE_BASKET_SETTINGS):
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        basket = get_basket(request, "basket")
        basket.customer = get_person_contact(admin_user)
        assert basket_commands.handle_set_customer(request, basket, AnonymousContact())["ok"] is True
        assert basket.customer == AnonymousContact()
        assert basket.orderer == AnonymousContact()
        assert basket.creator == admin_user


@pytest.mark.django_db
def test_set_from_anonymous_to_customer_not_auth(rf):
    """
    Set some customer to the basket when not authenticated
    """
    with override_settings(**CORE_BASKET_SETTINGS):
        request = apply_request_middleware(rf.get("/"))
        basket = get_basket(request, "basket")
        basket.customer = AnonymousContact()

        customer = factories.create_random_person()
        assert basket_commands.handle_set_customer(request, basket, customer)["ok"] is True
        assert basket.customer == customer


@pytest.mark.django_db
def test_set_from_anonymous_to_customer_auth(rf):
    """
    Set some random customer to the basket when authenticated
    """
    with override_settings(**CORE_BASKET_SETTINGS):
        user = factories.create_random_user()
        request = apply_request_middleware(rf.get("/"), user=user)
        basket = get_basket(request, "basket")
        basket.customer = AnonymousContact()

        # can not set the customer for something different as the request customer
        with pytest.raises(ValidationError) as exc:
            basket_commands.handle_set_customer(request, basket, factories.create_random_person())
        assert exc.value.code == "no_permission"
        assert basket.customer == AnonymousContact()

        assert basket_commands.handle_set_customer(request, basket, get_person_contact(user))["ok"] is True
        assert basket.customer == get_person_contact(user)


@pytest.mark.django_db
def test_set_not_active_customer(rf):
    """
    Set a not active customer to the basket
    """
    with override_settings(**CORE_BASKET_SETTINGS):
        user = factories.create_random_user()
        request = apply_request_middleware(rf.get("/"), user=user)
        basket = get_basket(request, "basket")
        basket.customer = get_person_contact(user)

        person = factories.create_random_person()
        person.is_active = False
        person.save()

        company = factories.create_random_company()
        company.is_active = False
        company.save()

        for customer in [person, company]:
            with pytest.raises(ValidationError) as exc:
                basket_commands.handle_set_customer(request, basket, customer)
            assert exc.value.code == "invalid_customer"
            assert basket.customer == get_person_contact(user)


@pytest.mark.django_db
def test_set_non_shop_member_customer(rf):
    """
    Set some customer to the basket that is not member of the shop
    """
    with override_settings(**CORE_BASKET_SETTINGS):
        shop = factories.get_shop(False)
        assert shop != factories.get_default_shop()

        user = factories.create_random_user()
        request = apply_request_middleware(rf.get("/"), user=user)
        basket = get_basket(request, "basket")
        basket.customer = get_person_contact(user)
        assert basket.shop == factories.get_default_shop()

        person = factories.create_random_person()
        person.shops.add(shop)

        company = factories.create_random_company()
        company.shops.add(shop)

        for customer in [person, company]:
            with pytest.raises(ValidationError) as exc:
                basket_commands.handle_set_customer(request, basket, customer)
            assert exc.value.code == "invalid_customer_shop"
            assert basket.customer == get_person_contact(user)


@pytest.mark.django_db
def test_set_different_customer(rf):
    """
    Set some customer to the basket that is not the request one
    """
    with override_settings(**CORE_BASKET_SETTINGS):
        user = factories.create_random_user()
        request = apply_request_middleware(rf.get("/"), user=user)
        basket = get_basket(request, "basket")
        basket.customer = get_person_contact(user)
        person1 = factories.create_random_person()

        with pytest.raises(ValidationError) as exc:
            basket_commands.handle_set_customer(request, basket, person1)
        assert exc.value.code == "no_permission"
        assert basket.customer == get_person_contact(user)

        # with superuser
        person2 = factories.create_random_person()
        superuser = factories.create_random_user(is_superuser=True)
        request = apply_request_middleware(rf.get("/"), user=superuser)
        assert basket_commands.handle_set_customer(request, basket, person2)["ok"] is True
        assert basket.customer == person2
        assert basket.orderer == person2

        # with staff user not member of the shop
        person3 = factories.create_random_person()
        staff = factories.create_random_user(is_staff=True)
        request = apply_request_middleware(rf.get("/"), user=staff)
        with pytest.raises(ValidationError) as exc:
            basket_commands.handle_set_customer(request, basket, person3)
        assert exc.value.code == "no_permission"
        assert basket.customer == person2
        assert basket.orderer == person2

        # with staff user member of the shop
        person4 = factories.create_random_person()
        staff_member = factories.create_random_user(is_staff=True)
        basket.shop.staff_members.add(staff_member)
        request = apply_request_middleware(rf.get("/"), user=staff_member)
        assert basket_commands.handle_set_customer(request, basket, person4)["ok"] is True
        assert basket.customer == person4
        assert basket.orderer == person4


@pytest.mark.django_db
def test_set_company_customer(rf):
    """
    Set a company as the basket customer
    """
    with override_settings(**CORE_BASKET_SETTINGS):
        user = factories.create_random_user()
        request = apply_request_middleware(rf.get("/"), user=user)
        basket = get_basket(request, "basket")
        basket.customer = get_person_contact(user)

        person = factories.create_random_person()
        company = factories.create_random_company()

        # no orderer provided
        with pytest.raises(ValidationError) as exc:
            basket_commands.handle_set_customer(request, basket, company)
        assert exc.value.code == "invalid_orderer"
        assert basket.customer == get_person_contact(user)

        # orderer provided but not member of the company
        with pytest.raises(ValidationError) as exc:
            basket_commands.handle_set_customer(request, basket, company, person)
        assert exc.value.code == "orderer_not_company_member"
        assert basket.customer == get_person_contact(user)

        # orderer provided but user not member of the company
        company.members.add(person)
        with pytest.raises(ValidationError) as exc:
            basket_commands.handle_set_customer(request, basket, company, person)
        assert exc.value.code == "not_company_member"
        assert basket.customer == get_person_contact(user)

        # staff and admin can add any the company and orderer without being member of the company
        superuser = factories.create_random_user(is_superuser=True)
        staff = factories.create_random_user(is_staff=True)
        basket.shop.staff_members.add(staff)

        for user in [superuser, staff]:
            basket.customer = None
            basket.orderer = None

            request = apply_request_middleware(rf.get("/"), user=user)
            assert basket_commands.handle_set_customer(request, basket, company, person)["ok"] is True
            assert basket.customer == company
            assert basket.orderer == person


@pytest.mark.django_db
def test_anonymous_set_company_customer(rf):
    """
    Set a company as the basket customer
    """
    with override_settings(**CORE_BASKET_SETTINGS):
        user = factories.create_random_user()
        request = apply_request_middleware(rf.get("/"), user=user)
        basket = get_basket(request, "basket")
        basket.customer = AnonymousContact()

        person = factories.create_random_person()
        company = factories.create_random_company()
        company.members.add(person)

        with pytest.raises(ValidationError) as exc:
            basket_commands.handle_set_customer(request, basket, company, person)
        assert exc.value.code == "not_company_member"
        assert basket.customer == AnonymousContact()
