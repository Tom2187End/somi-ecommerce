# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import datetime

from django.utils.timezone import now
import pytest
from shoop.simple_cms.models import Page
from shoop_tests.simple_cms.utils import create_page


@pytest.mark.django_db
def test_none_dates_page_not_visible():
    # create page that is not anymore visible
    page = create_page()

    assert not Page.objects.visible().filter(pk=page.pk).exists()
    assert not page.is_visible()


@pytest.mark.django_db
def test_past_page_not_visible():
    today = now()
    page = create_page(
        available_from=(today - datetime.timedelta(days=2)),
        available_to=(today - datetime.timedelta(days=1)),
    )
    assert not Page.objects.visible().filter(pk=page.pk).exists()
    assert not page.is_visible()


@pytest.mark.django_db
def test_future_page_not_visible():
    today = now()
    page = create_page(
        available_from=(today + datetime.timedelta(days=1)),
        available_to=(today + datetime.timedelta(days=2)),
    )
    assert not Page.objects.visible().filter(pk=page.pk).exists()
    assert not page.is_visible()


@pytest.mark.django_db
def test_current_page_is_visible():
    today = now()
    page = create_page(available_from=today, available_to=today)

    assert Page.objects.visible(today).filter(pk=page.pk).exists()
    assert page.is_visible(today)


@pytest.mark.django_db
def test_page_without_visibility_end_is_visible():
    today = now()
    page = create_page(available_from=today, available_to=None)

    assert Page.objects.visible(today).filter(pk=page.pk).exists()
    assert page.is_visible(today)


