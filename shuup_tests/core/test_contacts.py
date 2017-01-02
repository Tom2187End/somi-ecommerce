# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet
from shuup import configuration

from shuup.core.models import (
    AnonymousContact, CompanyContact, ContactGroup, get_company_contact,
    get_person_contact, PersonContact
)
from shuup.core.pricing import PriceDisplayOptions
from shuup.testing.factories import create_random_company, get_all_seeing_key
from shuup_tests.utils.fixtures import regular_user


@pytest.mark.django_db
def test_omniscience(admin_user, regular_user):
    assert not get_person_contact(admin_user).is_all_seeing
    configuration.set(None, get_all_seeing_key(admin_user), True)
    assert get_person_contact(admin_user).is_all_seeing
    assert not get_person_contact(regular_user).is_all_seeing
    assert not get_person_contact(None).is_all_seeing
    assert not get_person_contact(AnonymousUser()).is_all_seeing
    assert not AnonymousContact().is_all_seeing
    configuration.set(None, get_all_seeing_key(admin_user), False)


@pytest.mark.django_db
def test_anonymity(admin_user, regular_user):
    assert not get_person_contact(admin_user).is_anonymous
    assert not get_person_contact(regular_user).is_anonymous
    assert get_person_contact(None).is_anonymous
    assert get_person_contact(AnonymousUser()).is_anonymous
    assert AnonymousContact().is_anonymous


@pytest.mark.django_db
def test_anonymous_contact():
    a1 = AnonymousContact()
    a2 = AnonymousContact()

    # Basic Contact stuff
    assert a1.is_anonymous, "AnonymousContact is anonymous"
    assert not a1.is_all_seeing, "AnonymousContact is not all seeing"
    assert a1.identifier is None
    assert a1.is_active, "AnonymousContact is active"
    assert a1.language == ''
    assert a1.marketing_permission
    assert a1.phone == ''
    assert a1.www == ''
    assert a1.timezone is None
    assert a1.prefix == ''
    assert a1.name == '', "AnonymousContact has no name"
    assert a1.suffix == ''
    assert a1.name_ext == ''
    assert a1.email == '', "AnonymousContact has no email"
    assert str(a1) == ''

    # Primary key / id
    assert a1.pk is None
    assert a1.id is None

    # AnonymousContact instance evaluates as false
    assert not a1

    # All AnonymousContacts should be equal
    assert a1 == a2

    # Cannot be saved
    with pytest.raises(NotImplementedError):
        a1.save()

    # Cannot be deleted
    with pytest.raises(NotImplementedError):
        a1.delete()

    assert isinstance(a1.groups, QuerySet)
    assert a1.groups.first().identifier == AnonymousContact.default_contact_group_identifier
    assert a1.groups.count() == 1
    assert len(a1.groups.all()) == 1


@pytest.mark.django_db
def test_anonymous_contact_vs_person(regular_user):
    anon = AnonymousContact()
    person = get_person_contact(regular_user)
    assert anon != person
    assert person != anon


@pytest.mark.django_db
def test_person_contact_creating_from_user(regular_user):
    user = regular_user
    user.first_name = 'Joe'
    user.last_name = 'Regular'

    # Preconditions
    assert user.get_full_name()
    assert not PersonContact.objects.filter(user=user).exists()

    # Actual test
    person = get_person_contact(user)
    assert person.is_active == user.is_active
    assert person.name == user.get_full_name()
    assert person.email == user.email


@pytest.mark.django_db
def test_person_name_init_by_name():
    john = PersonContact(name="John Smith")
    assert john.name == "John Smith"
    assert john.first_name == "John"
    assert john.last_name == "Smith"


@pytest.mark.django_db
def test_person_name_create_with_name():
    john = PersonContact.objects.create(name="John Smith")
    assert PersonContact.objects.get(pk=john.pk).name == "John Smith"
    assert john.name == "John Smith"
    assert john.first_name == "John"
    assert john.last_name == "Smith"


@pytest.mark.django_db
def test_person_name_init_by_first_and_last_name():
    john = PersonContact(first_name="John", last_name="Smith")
    assert john.name == "John Smith"
    assert john.first_name == "John"
    assert john.last_name == "Smith"


@pytest.mark.django_db
def test_company_contact_name_ext():
    company = CompanyContact(name="TestCompany")
    assert company.name == "TestCompany"
    assert company.full_name == "TestCompany"
    company.name_ext = "California"
    company.save()
    assert company.name == "TestCompany"
    assert company.full_name == "TestCompany / California"


@pytest.mark.django_db
def test_person_name_gets_saved():
    john = PersonContact.objects.create(first_name="John", last_name="Smith")
    assert john.name == "John Smith"
    assert john in set(PersonContact.objects.filter(name="John Smith"))
    john.last_name = "Doe"
    assert john.name == "John Doe"
    john.save()
    assert john.name == "John Doe"
    assert john in set(PersonContact.objects.filter(name="John Doe"))
    assert john not in set(PersonContact.objects.filter(name="John Smith"))


def test_contact_group_repr_and_str_no_identifier_no_name():
    cg = ContactGroup()
    assert repr(cg) == '<ContactGroup:None>'
    assert str(cg) == 'contact group'


def test_contact_group_repr_and_str_has_identifier_no_name():
    cg = ContactGroup(identifier='hello')
    assert repr(cg) == '<ContactGroup:None-hello>'
    assert str(cg) == 'contact group "hello"'


def test_contact_group_repr_and_str_no_identifier_has_name():
    cg = ContactGroup(name='world')
    assert repr(cg) == '<ContactGroup:None>'
    assert str(cg) == 'world'


def test_contact_group_repr_and_str_has_identifier_has_name():
    cg = ContactGroup(identifier='hello', name='world')
    assert repr(cg) == '<ContactGroup:None-hello>'
    assert str(cg) == 'world'


@pytest.mark.django_db
def test_default_anonymous_contact_group_repr_and_str():
    adg = AnonymousContact.get_default_group()
    assert repr(adg) == '<ContactGroup:%d-default_anonymous_group>' % adg.pk
    assert str(adg) == 'Anonymous Contacts'


@pytest.mark.django_db
def test_default_company_contact_group_repr_and_str():
    cdg = CompanyContact.get_default_group()
    assert repr(cdg) == '<ContactGroup:%d-default_company_group>' % cdg.pk
    assert str(cdg) == 'Company Contacts'


@pytest.mark.django_db
def test_default_person_contact_group_repr_and_str():
    pdg = PersonContact.get_default_group()
    assert repr(pdg) == '<ContactGroup:%d-default_person_group>' % pdg.pk
    assert str(pdg) == 'Person Contacts'


@pytest.mark.django_db
def test_contact_group_price_display_options_filtering():
    cg0 = ContactGroup.objects.create()
    cg1 = ContactGroup.objects.create(hide_prices=True)
    cg2 = ContactGroup.objects.create(hide_prices=False)
    cg3 = ContactGroup.objects.create(show_prices_including_taxes=True)
    cg4 = ContactGroup.objects.create(show_prices_including_taxes=False)
    groups_qs = ContactGroup.objects.with_price_display_options()
    assert isinstance(groups_qs, QuerySet)
    groups = list(groups_qs)
    assert cg0 not in groups
    assert cg1 in groups
    assert cg2 in groups
    assert cg3 in groups
    assert cg4 in groups


def test_contact_group_price_display_options_defaults():
    options = ContactGroup().get_price_display_options()
    assert isinstance(options, PriceDisplayOptions)
    assert options.include_taxes is None
    assert options.show_prices is True


@pytest.mark.parametrize("taxes", [True, False, None])
@pytest.mark.parametrize("hide_prices", [True, False, None])
def test_contact_group_price_display_options_defined(taxes, hide_prices):
    options = ContactGroup(
        show_prices_including_taxes=taxes,
        hide_prices=hide_prices,
    ).get_price_display_options()
    assert isinstance(options, PriceDisplayOptions)
    assert options.include_taxes is taxes
    assert options.hide_prices is bool(hide_prices)
    assert options.show_prices is bool(not hide_prices)


@pytest.mark.django_db
def test_contact_group_price_display_for_contact(regular_user):
    group = ContactGroup.objects.create(hide_prices=True)
    person = get_person_contact(regular_user)
    person.groups.add(group)

    options = person.get_price_display_options()
    assert options.hide_prices
    assert options.include_taxes is None

    default_group_for_person = person.get_default_group()
    default_group_for_person.show_prices_including_taxes = True
    default_group_for_person.save()

    # Now since default group has pricing options set these should be returned
    default_options = person.get_price_display_options()
    assert default_options.include_taxes
    assert not default_options.hide_prices


@pytest.mark.django_db
def test_get_company_contact(regular_user):
    person_contact = get_person_contact(regular_user)
    assert person_contact != AnonymousContact()
    assert not get_company_contact(regular_user)

    company_contact = create_random_company()
    company_contact.members.add(person_contact)
    assert get_company_contact(regular_user) == company_contact
