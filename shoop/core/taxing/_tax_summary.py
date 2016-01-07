# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from collections import defaultdict
from decimal import Decimal

from django.utils.translation import ugettext as _

from shoop.utils.money import Money

from ._line_tax import LineTax


class TaxSummary(list):
    @classmethod
    def from_line_taxes(cls, line_taxes, untaxed):
        """
        Create TaxSummary from LineTaxes.

        :param line_taxes: List of line taxes to summarize
        :type line_taxes: list[LineTax]
        :param untaxed: Sum of taxless prices that have no taxes added
        :type untaxed: shoop.core.pricing.TaxlessPrice
        """
        zero_amount = Money(0, untaxed.currency)
        tax_amount_by_tax = defaultdict(lambda: zero_amount)
        base_amount_by_tax = defaultdict(lambda: zero_amount)
        for line_tax in line_taxes:
            assert isinstance(line_tax, LineTax)
            tax_amount_by_tax[line_tax.tax] += line_tax.amount
            base_amount_by_tax[line_tax.tax] += line_tax.base_amount

        lines = [
            TaxSummaryLine.from_tax(tax, base_amount_by_tax[tax], tax_amount)
            for (tax, tax_amount) in tax_amount_by_tax.items()
        ]
        if untaxed:
            lines.append(
                TaxSummaryLine(
                    tax_id=None, tax_code='', tax_name=_("Untaxed"),
                    tax_rate=Decimal(0), based_on=untaxed.amount,
                    tax_amount=zero_amount))
        return cls(sorted(lines, key=(lambda x: (x.tax_rate or 0))))

    def __repr__(self):
        super_repr = super(TaxSummary, self).__repr__()
        return '%s(%s)' % (type(self).__name__, super_repr)


class TaxSummaryLine(object):
    @classmethod
    def from_tax(cls, tax, based_on, tax_amount):
        return cls(
            tax_id=tax.id, tax_code=tax.code, tax_name=tax.name,
            tax_rate=tax.rate, based_on=based_on, tax_amount=tax_amount)

    def __init__(self, tax_id, tax_code, tax_name, tax_rate,
                 based_on, tax_amount):
        self.tax_id = tax_id
        self.tax_code = tax_code
        self.tax_name = tax_name
        self.tax_rate = tax_rate
        self.based_on = based_on
        self.tax_amount = tax_amount
        self.taxful = based_on + tax_amount

    def __repr__(self):
        return '<{} {}/{}/{:.3%} based_on={} tax_amount={})>'.format(
            type(self).__name__,
            self.tax_id, self.tax_code, float(self.tax_rate or 0),
            self.based_on, self.tax_amount)
