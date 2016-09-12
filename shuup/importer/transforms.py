# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import sys

import openpyxl
import six
import xlrd
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup.utils.excs import Problem

if sys.version_info >= (3, 0):
    import csv
else:
    import unicodecsv as csv


class RowYielder(object):
    def __init__(self, sheet_or_data):
        self.sheet_or_data = sheet_or_data

    def transform_values(self, row):
        return row


class XLSRowYielder(RowYielder):
    def __iter__(self):
        for y in range(self.sheet_or_data.nrows):
            yield self.transform_values(self.sheet_or_data.row_values(y))


class XLSXRowYielder(RowYielder):
    def __iter__(self):
        for row in self.sheet_or_data.rows:
            yield self.transform_values([cell.value for cell in row])


class TransformedData(object):
    def __init__(self, mode, headers, rows, **meta):
        self.mode = mode
        self.headers = headers
        self.meta = meta
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)

    def __getitem__(self, key):
        return self.rows[key]

    def __len__(self):
        return len(self.rows)


def process_data(rows):
    headers = []
    got_data = set()
    data = []
    if not len(data):
        for y, row in enumerate(rows):
            if y == 0:
                headers = [x.lower().strip() for x in row]
                continue
            datum = dict(zip(headers, row))
            got_data.update(set(h for (h, d) in six.iteritems(datum) if d))
            data.append(datum)

    row_limit = getattr(settings, "IMPORT_MAX_ROWS", 1000)
    if len(data) > row_limit:
        raise Problem(_("Cannot import more than %s rows from one file.") % row_limit)
    return (data, got_data)


def transform_file(mode, filename, data=None):
    meta = {}

    if mode == "xls":
        wb = xlrd.open_workbook(filename, file_contents=data, on_demand=True, formatting_info=True)
        sheet = wb.get_sheet(0)
        data, got_data = process_data(rows=XLSRowYielder(sheet))
        meta["xls_datemode"] = wb.datemode
    elif mode == "xlsx":
        wb = openpyxl.load_workbook(filename)
        sheet = wb.worksheets[0]
        data, got_data = process_data(rows=XLSXRowYielder(sheet))
    elif mode == "csv":
        # for python2 http://stackoverflow.com/questions/904041/reading-a-utf8-csv-file-with-python/14786752#14786752
        if sys.version_info >= (3, 0):
            data, got_data = py3_read_file(data, filename)
        else:
            data, got_data = py2_read_file(data, filename)
    else:
        raise NotImplementedError("Mode %s Not implemented" % mode)

    headers = data[0].keys() if len(data) else []
    clean_keys = set(headers) - got_data

    for datum in data:
        for key in clean_keys:
            datum.pop(key, None)

    return TransformedData(mode, headers, data, **meta)


def py2_read_file(data, filename):
    got_data = set()
    data = []
    with open(filename) as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        for x, row in enumerate(csv.DictReader(f, dialect=dialect)):
            got_data.update(set(h for (h, d) in six.iteritems(row) if d))
            data.append(row)
    return data, got_data


def py3_read_file(data, filename):
    got_data = set()
    data = []
    with open(filename, encoding="utf-8") as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        for x, row in enumerate(csv.DictReader(f, dialect=dialect)):
            got_data.update(set(h for (h, d) in six.iteritems(row) if d))
            data.append(row)
    return data, got_data
