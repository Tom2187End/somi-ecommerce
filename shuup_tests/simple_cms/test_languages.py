# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.utils import translation

from shuup.simple_cms.models import Page
from shuup_tests.simple_cms.utils import create_multilanguage_page


@pytest.mark.django_db
def test_create_multilanguage_page():
    with translation.override("de"):
        page_id = create_multilanguage_page(url="multi").pk

        with translation.override("fi"):
            page = Page.objects.get(pk=page_id)
            assert page.title == "test, Finnisch"
            assert page.url == "multi-fi"

        with translation.override("en"):
            page = Page.objects.get(pk=page_id)
            assert page.title == "test, Englisch"
            assert page.url == "multi-en"
