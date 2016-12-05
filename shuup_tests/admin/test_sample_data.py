# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.urlresolvers import reverse

from shuup import configuration
from shuup.admin.modules.sample_data import manager
from shuup.admin.modules.sample_data.data import BUSINESS_SEGMENTS, CMS_PAGES
from shuup.admin.modules.sample_data.forms import (
    ConsolidateObjectsForm, SampleObjectsWizardForm
)
from shuup.admin.modules.sample_data.views import ConsolidateSampleObjectsView
from shuup.admin.views.dashboard import DashboardView
from shuup.admin.views.wizard import WizardView
from shuup.core.models import AnonymousContact, Category, Product, Shop
from shuup.front.apps.carousel.models import Carousel, Slide
from shuup.front.apps.carousel.plugins import CarouselPlugin
from shuup.simple_cms.models import Page
from shuup.testing.factories import (
    CategoryFactory, get_default_shop, get_default_supplier,
    get_default_tax_class, ProductFactory
)
from shuup.testing.utils import apply_request_middleware
from shuup.xtheme.models import SavedViewConfig


@pytest.mark.django_db
def test_sample_data_manager():
    shop = get_default_shop()

    assert manager.get_installed_products(shop) == []
    assert manager.get_installed_categories(shop) == []
    assert manager.get_installed_cms_pages(shop) == []
    assert manager.get_installed_carousel(shop) is None
    assert manager.has_installed_samples(shop) is False

    PRODUCTS = [1, 2, 3]
    CATEGORIES = [4, 5, 6]
    CMS = ["about_us"]
    CAROUSEL = 1

    manager.save_categories(shop, CATEGORIES)
    manager.save_products(shop, PRODUCTS)
    manager.save_cms_pages(shop, CMS)
    manager.save_carousel(shop, CAROUSEL)

    assert manager.get_installed_products(shop) == PRODUCTS
    assert manager.get_installed_categories(shop) == CATEGORIES
    assert manager.get_installed_cms_pages(shop) == CMS
    assert manager.get_installed_carousel(shop) == CAROUSEL
    assert manager.has_installed_samples(shop) is True

    new_shop = Shop.objects.create()
    assert manager.get_installed_products(new_shop) == []
    assert manager.get_installed_categories(new_shop) == []
    assert manager.get_installed_cms_pages(new_shop) == []
    assert manager.get_installed_carousel(new_shop) is None
    assert manager.has_installed_samples(new_shop) is False

    manager.clear_installed_samples(shop)
    assert manager.get_installed_products(shop) == []
    assert manager.get_installed_categories(shop) == []
    assert manager.get_installed_cms_pages(shop) == []
    assert manager.get_installed_carousel(shop) is None
    assert manager.has_installed_samples(shop) is False


@pytest.mark.parametrize("with_simple_cms", [True, False])
@pytest.mark.django_db
def test_sample_data_wizard_pane(rf, admin_user, settings, with_simple_cms):
    settings.SHUUP_SETUP_WIZARD_PANE_SPEC = [
        "shuup.admin.modules.sample_data.views.SampleObjectsWizardPane"
    ]

    if not with_simple_cms:
        settings.INSTALLED_APPS.remove("shuup.simple_cms")

    shop = get_default_shop()
    get_default_tax_class()

    data = {
        'pane_id': 'sample',
        'sample-business_segment': 'default',
        'sample-categories': True,
        'sample-products': True,
        'sample-carousel': True
    }

    if with_simple_cms:
        data.update({"sample-cms": CMS_PAGES.keys()})

    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 200

    assert Product.objects.count() == len(BUSINESS_SEGMENTS["default"]["products"])
    anon_contact = AnonymousContact()
    supplier = get_default_supplier()

    # check for the injected plugin using the carousel
    assert Carousel.objects.count() == 1
    carousel = Carousel.objects.first()
    assert Slide.objects.count() == len(BUSINESS_SEGMENTS["default"]["carousel"]["slides"])
    svc = SavedViewConfig.objects.first()
    assert svc.view_name == "IndexView"
    layout = svc.get_layout_data("front_content")
    assert layout['rows'][0]['cells'][0]['config']['carousel'] == carousel.pk
    assert layout['rows'][0]['cells'][0]['plugin'] == CarouselPlugin.identifier

    for product in Product.objects.all():
        # all products must be orderable and have images
        assert product.get_shop_instance(shop).is_orderable(supplier=supplier,
                                                            customer=anon_contact,
                                                            quantity=1)
        assert product.primary_image is not None

    assert Category.objects.count() == len(BUSINESS_SEGMENTS["default"]["categories"])

    if with_simple_cms:
        assert Page.objects.count() == len(CMS_PAGES.keys())
        for page_id, content in CMS_PAGES.items():
            page = Page.objects.get(identifier=page_id)
            assert page.title == content["title"]
            assert page.content == content["content"]
    else:
        assert Page.objects.count() == 0
        settings.INSTALLED_APPS.append("shuup.simple_cms")

    request = apply_request_middleware(rf.get("/"))
    response = WizardView.as_view()(request)
    assert response.status_code == 302
    assert response["Location"] == reverse("shuup_admin:dashboard")


@pytest.mark.django_db
def test_forms(settings):
    # check wheter the cms field only appears when the module is installed
    settings.INSTALLED_APPS.remove("shuup.simple_cms")
    wizard_form = SampleObjectsWizardForm()
    assert "cms" not in wizard_form.fields.keys()

    settings.INSTALLED_APPS.append("shuup.simple_cms")
    wizard_form = SampleObjectsWizardForm()
    assert "cms" in wizard_form.fields.keys()

    # check whether the fields are dynamically added
    shop = get_default_shop()
    manager.clear_installed_samples(shop)
    consolidate_form = ConsolidateObjectsForm(**{"shop":shop})
    assert len(consolidate_form.fields) == 0

    # field categories appears
    categories = [CategoryFactory().pk, CategoryFactory().pk, CategoryFactory().pk]
    manager.save_categories(shop, categories)
    consolidate_form = ConsolidateObjectsForm(**{"shop":shop})
    assert "categories" in consolidate_form.fields

    # field products appears
    products = [ProductFactory().pk, ProductFactory().pk, ProductFactory().pk]
    manager.save_products(shop, products)
    consolidate_form = ConsolidateObjectsForm(**{"shop":shop})
    assert "products" in consolidate_form.fields

    # field carousel appears
    carousel = Carousel.objects.create(name="stuff")
    manager.save_carousel(shop, carousel.pk)
    consolidate_form = ConsolidateObjectsForm(**{"shop":shop})
    assert "carousel" in consolidate_form.fields

    # field cms appears
    cms_pages = [Page.objects.create(identifier="about_us", title="title").identifier]
    manager.save_cms_pages(shop, cms_pages)
    consolidate_form = ConsolidateObjectsForm(**{"shop":shop})
    assert "cms" in consolidate_form.fields


@pytest.mark.django_db
def test_admin(rf, admin_user):
    shop = get_default_shop()
    configuration.set(shop, "setup_wizard_complete", True)
    # just visit to make sure everything is ok
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = DashboardView.as_view()(request)
    assert response.status_code == 200

    categories = [CategoryFactory().pk, CategoryFactory().pk, CategoryFactory().pk]
    manager.save_categories(shop, categories)
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = DashboardView.as_view()(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_consolidate_objects(rf):
    shop = get_default_shop()

    # just visit to make sure GET is ok
    request = apply_request_middleware(rf.get("/"))
    response = ConsolidateSampleObjectsView.as_view()(request)
    assert response.status_code == 200

    def populate_samples():
        manager.clear_installed_samples(shop)
        categories = [CategoryFactory().pk, CategoryFactory().pk, CategoryFactory().pk]
        products = [ProductFactory().pk, ProductFactory().pk, ProductFactory().pk, ProductFactory().pk]
        cms_pages = [Page.objects.create(identifier="about_us", title="title").identifier]
        carousel = Carousel.objects.create(name="crazy stuff").pk
        manager.save_categories(shop, categories)
        manager.save_products(shop, products)
        manager.save_cms_pages(shop, cms_pages)
        manager.save_carousel(shop, carousel)

    def clear_objs():
        Product.objects.all().delete()
        Category.objects.all().delete()
        Page.objects.all().delete()
        Carousel.objects.all().delete()

    # consolidate everything
    populate_samples()
    data = {
        "categories": False,
        "products": False,
        "cms": False,
        "carousel": False
    }
    request = apply_request_middleware(rf.post("/", data=data))
    response = ConsolidateSampleObjectsView.as_view()(request)
    assert response.status_code == 302
    assert response["Location"] == reverse("shuup_admin:dashboard")
    assert Category.objects.count() == 3
    assert Product.objects.count() == 4
    assert Page.objects.count() == 1
    assert Carousel.objects.count() == 1
    assert manager.get_installed_products(shop) == []
    assert manager.get_installed_categories(shop) == []
    assert manager.get_installed_cms_pages(shop) == []
    assert manager.get_installed_carousel(shop) is None

    # consolidate nothing
    clear_objs()
    populate_samples()
    data = {
        "products": True,
        "cms": True,
        "categories": True,
        "carousel": True
    }
    request = apply_request_middleware(rf.post("/", data=data))
    response = ConsolidateSampleObjectsView.as_view()(request)
    assert response.status_code == 302
    assert response["Location"] == reverse("shuup_admin:dashboard")
    assert Category.objects.all_except_deleted().count() == 0
    assert Product.objects.all_except_deleted().count() == 0
    assert Page.objects.count() == 0
    assert Carousel.objects.count() == 0
    assert manager.get_installed_products(shop) == []
    assert manager.get_installed_categories(shop) == []
    assert manager.get_installed_cms_pages(shop) == []
    assert manager.get_installed_carousel(shop) is None

    # consolidate some
    clear_objs()
    populate_samples()
    data = {
        "products": False,
        "cms": True,
        "categories": False,
        "carousel": True
    }
    request = apply_request_middleware(rf.post("/", data=data))
    response = ConsolidateSampleObjectsView.as_view()(request)
    assert response.status_code == 302
    assert response["Location"] == reverse("shuup_admin:dashboard")
    assert Category.objects.all_except_deleted().count() == 3
    assert Product.objects.all_except_deleted().count() == 4
    assert Page.objects.count() == 0
    assert Carousel.objects.count() == 0
    assert manager.get_installed_products(shop) == []
    assert manager.get_installed_categories(shop) == []
    assert manager.get_installed_cms_pages(shop) == []
    assert manager.get_installed_carousel(shop) is None
