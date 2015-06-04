# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import set_urlconf, reverse
import pytest
from shoop.notify import Context
from shoop.notify.actions.notification import AddNotification
from shoop.notify.enums import Priority, RecipientType
from shoop.notify.models.notification import Notification
from shoop_tests.notify.utils import make_bind_data
from shoop_tests.utils import very_recently
from shoop_tests.utils.fixtures import regular_user

__all__ = ["regular_user"]  # fix qa kvetch

@pytest.mark.django_db
@pytest.mark.parametrize("specific_user", (False, True))
def test_notification(admin_user, specific_user):
    AddNotification(make_bind_data(
        variables={"priority": "priority"},
        constants={
            "message": "Hi {{ name }}!",
            "message_identifier": "hi mom",
            "url": "http://burymewithmymoney.com/",
            "recipient_type": (RecipientType.SPECIFIC_USER if specific_user else RecipientType.ADMINS),
            "recipient": (admin_user if specific_user else None),
            "priority": Priority.CRITICAL
        }
    )).execute(Context.from_variables(name="Justin Case"))
    notif = Notification.objects.last()
    assert isinstance(notif, Notification)
    if specific_user:
        assert notif.recipient == admin_user
        assert Notification.objects.unread_for_user(admin_user).get(pk=notif.pk)
    assert notif.identifier == "hi mom"
    assert notif.message == "Hi Justin Case!"
    assert notif.priority == Priority.CRITICAL
    assert notif.url == "http://burymewithmymoney.com/"
    with pytest.raises(ValueError):
        notif.url = "http://www.theuselessweb.com/"

    assert not notif.is_read
    notif.mark_read(admin_user)  # Once, for setting
    notif.mark_read(admin_user)  # Twice, for branch checking
    assert notif.marked_read_by == admin_user
    assert very_recently(notif.marked_read_on)


@pytest.mark.django_db
def test_no_notifs_for_anon(regular_user):
    assert not Notification.objects.for_user(regular_user).exists()
    assert not Notification.objects.for_user(AnonymousUser()).exists()


@pytest.mark.django_db
def test_misconfigured_add_notification_is_noop():
    n_notifs = Notification.objects.count()
    AddNotification(make_bind_data(
        constants={
            "recipient_type": RecipientType.SPECIFIC_USER,
            "message": "This'll never get delivered!",
        }
    )).execute(Context())
    assert Notification.objects.count() == n_notifs


def test_misconfigured_specific_notification_fails():
    with pytest.raises(ValueError):
        Notification.objects.create(recipient_type=RecipientType.SPECIFIC_USER)


@pytest.mark.django_db
def test_notification_reverse_url():
    try:
        set_urlconf("shoop_tests.notify.notification_test_urls")
        n = Notification()
        kwargs = dict(viewname="test", kwargs={"arg": "yes"})  # kwargs within kwargs, oh my
        n.set_reverse_url(**kwargs)
        n.save()
        with pytest.raises(ValueError):
            n.set_reverse_url()
        assert n.url == reverse(**kwargs)
    finally:
        set_urlconf(None)


def test_urlless_notification():
    assert not Notification().url
