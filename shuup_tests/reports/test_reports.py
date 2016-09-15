# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import itertools
import json

import pytest
from decimal import Decimal

from bs4 import BeautifulSoup
from babel.dates import format_date
from django.utils.encoding import force_text
from django.utils.safestring import SafeText
from django.utils.translation import ugettext_lazy as _

from shuup.apps.provides import override_provides
from shuup.core.models import Order
from shuup.core.pricing import TaxlessPrice, TaxfulPrice
from shuup.reports.admin_module.views import ReportView
from shuup.reports.forms import DateRangeChoices
from shuup.reports.report import ShuupReportBase
from shuup.reports.writer import get_writer_instance
from shuup.testing.factories import get_default_shop, create_order_with_product, get_default_product, \
    get_default_supplier
from shuup.testing.utils import apply_request_middleware
from shuup.utils.i18n import get_current_babel_locale


def initialize_report_test(product_price, product_count, tax_rate, line_count):
    shop = get_default_shop()
    product = get_default_product()
    supplier = get_default_supplier()
    expected_taxless_total = product_count * product_price
    expected_taxful_total = product_count * product_price * (1 + tax_rate)
    order = create_order_with_product(
        product=product, supplier=supplier, quantity=product_count,
        taxless_base_unit_price=product_price, tax_rate=tax_rate, n_lines=line_count, shop=shop)
    return expected_taxful_total, expected_taxless_total, shop, order


class TestSalesReport(ShuupReportBase):
    identifier = "test_sales_report"
    title = _("Sales Report")

    filename_template = "sales-report-%(time)s"
    schema = [
        {"key": "date", "title": _("Date")},
        {"key": "order_count", "title": _("Orders")},
        {"key": "product_count", "title": _("Products")},
        {"key": "taxless_total", "title": _("Taxless Total")},
        {"key": "taxful_total", "title": _("Taxful Total")},
    ]

    def get_objects(self):
        return Order.objects.filter(
            shop=self.shop, order_date__range=(self.start_date, self.end_date)).order_by("order_date")

    def extract_date(self, entity):
        # extracts the starting date from an entity
        return entity.order_date.date()

    def get_data(self):
        orders = self.get_objects().order_by("-order_date")
        data = []
        for order_date, orders_group in itertools.groupby(orders, key=self.extract_date):
            taxless_total = TaxlessPrice(0, currency=self.shop.currency)
            taxful_total = TaxfulPrice(0, currency=self.shop.currency)
            paid_total = TaxfulPrice(0, currency=self.shop.currency)
            product_count = 0
            order_count = 0
            for order in orders_group:
                taxless_total += order.taxless_total_price
                taxful_total += order.taxful_total_price
                product_count += sum(order.get_product_ids_and_quantities().values())
                order_count += 1
                if order.payment_date:
                    paid_total += order.taxful_total_price

            data.append({
                "date": format_date(order_date, format="short", locale=get_current_babel_locale()),
                "order_count": order_count,
                "product_count": int(product_count),
                "taxless_total": taxless_total,
                "taxful_total": taxful_total,
            })

        return self.get_return_data(data)


@pytest.mark.django_db
def test_reporting(rf):

    product_price = 100
    product_count = 2
    tax_rate = Decimal("0.10")
    line_count = 1

    expected_taxful_total, expected_taxless_total, shop, order = initialize_report_test(product_price, product_count, tax_rate, line_count)

    with override_provides("reports", [__name__ + ":TestSalesReport"]):
        data = {
            "report": TestSalesReport.get_name(),
            "shop": shop.pk,
            "date_range": DateRangeChoices.THIS_YEAR.value,
            "writer": "json",
            "force_download": 1,
        }

        view = ReportView.as_view()
        request = apply_request_middleware(rf.post("/", data=data))
        response = view(request)
        if hasattr(response, "render"):
            response.render()
        assert response.status_code == 200
        json_data = json.loads(response.content.decode("utf-8"))
        assert force_text(TestSalesReport.title) in json_data.get("heading")
        totals = json_data.get("tables")[0].get("totals")
        return_data = json_data.get("tables")[0].get("data")[0]
        assert int(totals.get("product_count", 0)) == product_count
        assert int(return_data.get("product_count", 0)) == product_count
        assert int(totals.get("order_count", 0)) == 1
        assert int(return_data.get("order_count", 0)) == 1
        assert str(expected_taxless_total) in totals.get("taxless_total", "0")
        assert str(expected_taxful_total) in totals.get("taxful_total", "0")

        # test report without downloading it
        data = {
            "report": TestSalesReport.get_name(),
            "shop": shop.pk,
            "date_range": DateRangeChoices.CUSTOM.value,
            "start_date": "2016-01-01",
            "end_date": "2017-01-01",
            "writer": "json",
        }

        request = apply_request_middleware(rf.post("/", data=data))
        response = view(request)
        assert response.status_code == 200

        soup = BeautifulSoup(response.render().content)
        assert force_text(TestSalesReport.title) in str(soup)
        assert str(expected_taxless_total) in str(soup)
        assert str(expected_taxful_total) in str(soup)


@pytest.mark.django_db
def test_html_writer(rf):
    expected_taxful_total, expected_taxless_total, shop, order = initialize_report_test(10, 1, 0, 1)
    data = {
        "report": TestSalesReport.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.THIS_YEAR,
        "writer": "html",
        "force_download": 1,
    }
    report = TestSalesReport(**data)
    writer = get_writer_instance(data["writer"])
    assert str(writer) == data["writer"]
    rendered_report = writer.render_report(report=report)

    soup = BeautifulSoup(rendered_report)
    assert force_text(TestSalesReport.title) in str(soup)
    assert str(expected_taxless_total) in str(soup)
    assert str(expected_taxful_total) in str(soup)

    rendered_report = writer.render_report(report=report, inline=True)
    assert type(rendered_report) == SafeText
    assert force_text(TestSalesReport.title) in rendered_report
    assert str(expected_taxless_total) in rendered_report
    assert str(expected_taxful_total) in rendered_report

