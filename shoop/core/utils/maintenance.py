# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

def maintenance_mode_exempt(view_func):
    """
    Make view ignore shop maintenance mode

    :param view_func: view attached to this decorator
    :return: view added with maintenance_mode_exempt attribute
    """
    view_func.maintenance_mode_exempt = True
    return view_func
