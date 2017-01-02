# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from bs4 import BeautifulSoup
from shuup import configuration
from shuup.core.models import get_person_contact
from shuup.front.views.index import IndexView
from shuup.testing.factories import get_default_shop, get_all_seeing_key
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils.fixtures import regular_user


def do_request_and_asserts(rf, contact, maintenance=False, expect_all_seeing=False, expect_toolbar=False):
    request = apply_request_middleware(rf.get("/"), user=contact.user, customer=contact)
    response = IndexView.as_view()(request)
    response.render()
    soup = BeautifulSoup(response.content)
    if expect_toolbar:
        toolbar = soup.find("nav", {"class": "navbar-admin-tools"})
        assert toolbar

    if maintenance:
        maintenance_class = "maintenance-on" if maintenance else "maintenance-off"
        assert soup.find("span", {"class": maintenance_class})

    texts = []
    for elem in soup.find_all("a"):
        texts.append(elem.text.strip())

    if contact.user.is_superuser:
        text = "Show only visible products and categories" if expect_all_seeing else "Show all products and categories"
        assert text in texts
    else:
        assert "Show only visible products and categories" not in texts
        assert "Show all products and categories" not in texts


@pytest.mark.django_db
def test_all_seeing_and_maintenance(rf, admin_user):
    shop = get_default_shop()
    shop.maintenance_mode = True
    shop.save()
    admin_contact = get_person_contact(admin_user)
    do_request_and_asserts(rf, admin_contact, maintenance=True, expect_toolbar=True)

    shop.maintenance_mode = False
    shop.save()
    do_request_and_asserts(rf, admin_contact, maintenance=False, expect_toolbar=True)

    assert not admin_contact.is_all_seeing
    configuration.set(None, get_all_seeing_key(admin_user), True)
    # refresh cache
    del admin_contact.is_all_seeing
    assert admin_contact.is_all_seeing

    do_request_and_asserts(rf, admin_contact, maintenance=False, expect_all_seeing=True, expect_toolbar=True)
    configuration.set(None, get_all_seeing_key(admin_contact), False)


def test_regular_user_is_blind(rf, regular_user):
    shop = get_default_shop()
    contact = get_person_contact(regular_user)
    do_request_and_asserts(rf, contact, maintenance=False, expect_all_seeing=False, expect_toolbar=False)

    # user needs to be superuser to even get a glimpse
    assert not contact.is_all_seeing
    configuration.set(None, get_all_seeing_key(contact), True)
    assert not contact.is_all_seeing  # only superusers can be allseeing

    # Contact might be all-seeing in database but toolbar requires superuser
    do_request_and_asserts(rf, contact, maintenance=False, expect_all_seeing=False, expect_toolbar=False)
