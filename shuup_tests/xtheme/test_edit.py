# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.xtheme.editing import could_edit, is_edit_mode, set_edit_mode
from shuup_tests.utils.faux_users import SuperUser


def test_edit_priv(rf):
    request = rf.get("/")
    request.user = SuperUser()
    request.session = {}
    assert could_edit(request)
    assert not is_edit_mode(request)
    set_edit_mode(request, True)
    assert is_edit_mode(request)
    set_edit_mode(request, False)
    assert not is_edit_mode(request)
