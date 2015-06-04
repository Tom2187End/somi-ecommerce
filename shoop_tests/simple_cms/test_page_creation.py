# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
import pytest
from shoop.simple_cms.admin_module.views import PageForm, PageEditView
from shoop_tests.simple_cms.utils import create_page, create_multilanguage_page
from shoop_tests.utils.forms import get_form_data


@pytest.mark.django_db
def test_url_uniqueness(rf):
    page = create_page(url='bacon')
    with pytest.raises(ValidationError):
        page = create_page(url='bacon')

    with transaction.atomic():
        mpage = create_multilanguage_page(url="cheese")
        with pytest.raises(IntegrityError):
            mpage = create_multilanguage_page(url="cheese")


@pytest.mark.django_db
def test_page_form(rf):
    view = PageEditView(request=rf.get("/"))
    form_class = view.get_form_class()
    form_kwargs = view.get_form_kwargs()
    form = form_class(**form_kwargs)
    assert not form.is_bound

    data = get_form_data(form)
    data.update({
        "available_from": "",
        "available_to": "",
        "content__en": "",
        "content__fi": "suomi",
        "content__ja": "",
        "identifier": "",
        "title__en": "",
        "title__fi": "",
        "title__ja": "",
        "url__en": "",
        "url__fi": "suomi",
        "url__ja": "",
    })

    form = form_class(**dict(form_kwargs, data=data))
    form.full_clean()
    assert "title__fi" in form.errors  # We get an error because all of a given language's fields must be filled if any are
    data["title__fi"] = "suomi"
    form = form_class(**dict(form_kwargs, data=data))
    form.full_clean()
    assert not form.errors
    page = form.save()
    assert set(page.get_available_languages()) == {"fi"}  # The page should be only in Finnish
    # Let's edit that page
    data.update({"title__en": "englaish", "url__en": "errrnglish", "content__en": "ennnn ennnn ennnnnnn-nn-n-n"})
    form = form_class(**dict(form_kwargs, data=data, instance=page))
    form.full_clean()
    assert not form.errors
    page = form.save()
    assert set(page.get_available_languages()) == {"fi", "en"}  # English GET
