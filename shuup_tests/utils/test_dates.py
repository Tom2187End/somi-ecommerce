# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from datetime import date, datetime
from shuup.utils.dates import parse_date


def test_parse_date():
    now = datetime.now()
    today = date.today()

    date_fmt1 = "2016-12-31"
    date_fmt2 = "2016-12-31 15:40:34.404540"
    date_fmt3 = "12/31/2016"
    expected_date = date(2016, 12, 31)

    assert parse_date(now) == now.date()
    assert parse_date(today) == today
    assert parse_date(date_fmt1) == expected_date
    assert parse_date(date_fmt2) == expected_date
    assert parse_date(date_fmt3) == expected_date
