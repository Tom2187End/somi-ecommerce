# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet

from shoop.core.models import (
    AnonymousContact, CompanyContact, ContactGroup, get_person_contact,
    PersonContact
)
from shoop_tests.utils.fixtures import regular_user


@pytest.mark.django_db
def test_omniscience(admin_user, regular_user):
    assert get_person_contact(admin_user).is_all_seeing
    assert not get_person_contact(regular_user).is_all_seeing
    assert not get_person_contact(None).is_all_seeing
    assert not get_person_contact(AnonymousUser()).is_all_seeing
    assert not AnonymousContact().is_all_seeing


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
    assert a1.identifier is None
    assert a1.is_active
    assert a1.language == ''
    assert a1.marketing_permission
    assert a1.phone == ''
    assert a1.www == ''
    assert a1.timezone is None
    assert a1.prefix == ''
    assert a1.name == ''
    assert a1.suffix == ''
    assert a1.name_ext == ''
    assert a1.email == ''
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


def test_contact_group_repr_and_str_no_identifier_no_name():
    cg = ContactGroup()
    assert repr(cg) == '<ContactGroup:None>'
    assert str(cg) == 'Group<None>'


def test_contact_group_repr_and_str_has_identifier_no_name():
    cg = ContactGroup(identifier='hello')
    assert repr(cg) == '<ContactGroup:None-hello>'
    assert str(cg) == 'Group<hello>'


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
