# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.notify import Event
from shuup_tests.notify.fixtures import ATestEvent, get_initialized_test_event


@pytest.mark.django_db
def test_event_init():
    assert get_initialized_test_event().variable_values


def test_extra_vars_fails():
    with pytest.raises(ValueError):
        ATestEvent(not_valid=True)


def test_missing_vars_fails():
    with pytest.raises(ValueError):
        ATestEvent(just_some_text="Hello")


def test_init_empty_fails():
    with pytest.raises(ValueError):
        Event()

def test_auto_name():
    assert ATestEvent.name == "Test Event"
