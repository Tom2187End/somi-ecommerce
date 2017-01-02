# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.utils.translation import activate

from shuup.core.models import Product
from shuup.importer.admin_module.import_views import ImportView
from shuup.importer.utils.importer import ImportMode
from shuup.testing.factories import (
    get_default_product_type, get_default_shop, get_default_tax_class
)
from shuup_tests.utils import SmartClient

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
     from urlparse import urlparse, parse_qs

def do_importing(sku, name, lang, shop, import_mode=ImportMode.CREATE_UPDATE, client=None):

    is_update = True
    import_path = reverse("shuup_admin:importer.import")
    process_path = reverse("shuup_admin:importer.import_process")
    original_product = None
    if not client:
        is_update = False
        client = SmartClient()
        client.login(username="admin", password="password")
    else:
        p = Product.objects.get(sku=sku)
        p.set_current_language(lang)
        original_name = p.name
        original_sku = p.sku
    csv_content = str.encode("sku;name\n%s;%s" % (sku, name))
    # show import view

    data = {
        "importer": "product_importer",
        "shop": shop.pk,
        "language": lang,
        "file": SimpleUploadedFile("file.csv", csv_content, content_type="text/csv")
    }
    response = client.post(import_path, data=data)
    assert response.status_code == 302
    query_string = urlparse(response["location"]).query
    query = parse_qs(query_string)

    data = {
        "importer": "product_importer",
        "shop": shop.pk,
        "language": lang,
        "n": query.get("n"),
    }
    soup = client.soup(process_path, data=data)
    for row in soup.findAll("tr"):
        first_td = row.find("td")
        if not first_td:
            continue

        tds = row.findAll("td")
        if len(tds) < 2:
            continue
        second_td = tds[1]
        if first_td.text.startswith("Connection"):
            # check that sku was connected
            badges = second_td.findAll("span", {"class": "badge"})
            assert len(badges) == 1
            assert badges[0].text == "sku"
        elif first_td.text.startswith("The following fields"):
            badges = second_td.findAll("span", {"class": "badge"})
            assert len(badges) == 2
            badge_texts = []
            for b in badges:
                badge_texts.append(b.text)
            badge_texts.sort()
            assert badge_texts[0] == "name"
            assert badge_texts[1] == "sku"

    data = {}
    data["import_mode"] = import_mode.value
    process_submit_path = "%s?%s" % (process_path, query_string)
    client.soup(process_submit_path, data=data, method="post")

    assert Product.objects.count() == 1
    product = Product.objects.first()
    product.set_current_language(lang)
    if import_mode != ImportMode.CREATE:
        assert product.sku == sku
        assert product.name == name
    else:
        if is_update:
            assert product.sku == original_sku
            assert product.name == original_name
        else:
            assert product.sku == sku
            assert product.name == name
    return client


@pytest.mark.django_db
def test_admin(rf, admin_user):
    view = ImportView.as_view()
    activate("en")
    shop = get_default_shop()
    tax_class = get_default_tax_class()
    product_type = get_default_product_type()

    client = do_importing("123", "test", "en", shop)
    # change import language and update product
    client = do_importing("123", "test-fi", "fi", shop, client=client)

    # update name in english
    client = do_importing("123", "test-en", "en", shop, client=client)

    # cannot update
    client = do_importing("123", "test", "en", shop, import_mode=ImportMode.CREATE, client=client)

    # can update
    do_importing("123", "test", "en", shop, import_mode=ImportMode.UPDATE, client=client)


@pytest.mark.django_db
def test_invalid_files(rf, admin_user):
    lang = "en"
    import_mode = ImportMode.CREATE_UPDATE
    sku = "123"
    name = "test"

    import_path = reverse("shuup_admin:importer.import")
    process_path = reverse("shuup_admin:importer.import_process")
    tax_class = get_default_tax_class()
    product_type = get_default_product_type()

    activate("en")
    shop = get_default_shop()
    client = SmartClient()
    client.login(username="admin", password="password")
    csv_content = str.encode("sku;name\n%s;%s" % (sku, name))

    # show import view
    data = {
        "importer": "product_importer",
        "shop": shop.pk,
        "language": lang,
        "file": SimpleUploadedFile("file.csv", csv_content, content_type="text/csv")
    }
    response = client.post(import_path, data=data)
    assert response.status_code == 302
    query_string = urlparse(response["location"]).query
    query = parse_qs(query_string)

    data = { # data with missing `n`
        "importer": "product_importer",
        "shop": shop.pk,
        "language": lang,
    }
    soup = client.soup(process_path, data=data)
    assert "File missing." in str(soup)


def test_invalid_file_type(rf, admin_user):
    lang = "en"
    import_mode = ImportMode.CREATE_UPDATE
    sku = "123"
    name = "test"

    import_path = reverse("shuup_admin:importer.import")
    process_path = reverse("shuup_admin:importer.import_process")
    tax_class = get_default_tax_class()
    product_type = get_default_product_type()

    activate("en")
    shop = get_default_shop()
    client = SmartClient()
    client.login(username="admin", password="password")
    csv_content = str.encode("sku;name\n%s;%s" % (sku, name))

    # show import view
    data = {
        "importer": "product_importer",
        "shop": shop.pk,
        "language": lang,
        "file": SimpleUploadedFile("file.derp", csv_content, content_type="text/csv")
    }
    response = client.post(import_path, data=data)
    assert response.status_code == 302
    query_string = urlparse(response["location"]).query
    query = parse_qs(query_string)

    data = { # data with missing `n`
        "importer": "product_importer",
        "shop": shop.pk,
        "language": lang,
    }
    soup = client.soup(process_path, data=data)

    for row in soup.findAll("tr"):
        first_td = row.find("td")
        if not first_td:
            continue

        tds = row.findAll("td")
        if len(tds) < 2:
            continue
        second_td = tds[1]
        if first_td.text.startswith("Connection"):
            # check that sku was connected
            badges = second_td.findAll("span", {"class": "badge"})
            assert len(badges) == 1
            assert badges[0].text == "sku"
        elif first_td.text.startswith("The following fields"):
            badges = second_td.findAll("span", {"class": "badge"})
            assert len(badges) == 2
            badge_texts = []
            for b in badges:
                badge_texts.append(b.text)
            badge_texts.sort()
            assert badge_texts[0] == "name"
            assert badge_texts[1] == "sku"

    data = {}
    data["import_mode"] = import_mode.value
    process_submit_path = "%s?%s" % (process_path, query_string)
    response = client.post(process_submit_path, data=data)
    assert response.status_code == 302


@pytest.mark.django_db
def test_remap(rf, admin_user):
    lang = "en"
    import_mode = ImportMode.CREATE_UPDATE
    sku = "123"
    name = "test"

    import_path = reverse("shuup_admin:importer.import")
    process_path = reverse("shuup_admin:importer.import_process")
    tax_class = get_default_tax_class()
    product_type = get_default_product_type()

    activate("en")
    shop = get_default_shop()
    client = SmartClient()
    client.login(username="admin", password="password")
    csv_content = str.encode("sku;name;gtiin\n%s;%s;111" % (sku, name))

    # show import view
    data = {
        "importer": "product_importer",
        "shop": shop.pk,
        "language": lang,
        "file": SimpleUploadedFile("file.csv", csv_content, content_type="text/csv")
    }
    response = client.post(import_path, data=data)
    assert response.status_code == 302
    query_string = urlparse(response["location"]).query
    query = parse_qs(query_string)

    data = { # data with missing `n`
        "importer": "product_importer",
        "shop": shop.pk,
        "language": lang,
        "n": query.get("n")
    }
    soup = client.soup(process_path, data=data)
    assert "The following fields must be manually tied" in str(soup)

    for row in soup.findAll("tr"):
        first_td = row.find("td")
        if not first_td:
            continue

        tds = row.findAll("td")
        if len(tds) < 2:
            continue
        second_td = tds[1]
        if first_td.text.startswith("Connection"):
            # check that sku was connected
            badges = second_td.findAll("span", {"class": "badge"})
            assert len(badges) == 1
            assert badges[0].text == "sku"
        elif first_td.text.startswith("The following fields"):
            badges = second_td.findAll("span", {"class": "badge"})
            assert len(badges) == 2
            badge_texts = []
            for b in badges:
                badge_texts.append(b.text)
            badge_texts.sort()
            assert badge_texts[0] == "name"
            assert badge_texts[1] == "sku"

    data = {}
    data["import_mode"] = import_mode.value
    data["remap[gtiin]"] = "Product:gtin"  # map gtin
    process_submit_path = "%s?%s" % (process_path, query_string)
    client.soup(process_submit_path, data=data, method="post")
    assert Product.objects.count() == 1
    product = Product.objects.first()
    assert product.gtin == "111"
