# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import mock
from django.core.urlresolvers import reverse

from shuup.admin.template_helpers.shuup_admin import get_config
from shuup.testing.utils import apply_request_middleware
from shuup.admin.browser_config import DefaultBrowserConfigProvider


def test_get_config(rf, admin_user):
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    context = dict(request=request)
    config = get_config(context)
    for key, url in DefaultBrowserConfigProvider.get_browser_urls(request).items():
        if isinstance(url, tuple):
            assert config["browserUrls"][key] == reverse(url[0], args=url[1], kwargs=url[2])
        else:
            assert config["browserUrls"][key] == reverse(url)
    assert "minSearchInputLength" in DefaultBrowserConfigProvider.get_gettings(request).keys()
