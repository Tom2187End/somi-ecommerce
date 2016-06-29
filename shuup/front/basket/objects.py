# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import random
from collections import Counter
from decimal import Decimal

import six
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import OrderLineType, PaymentMethod, ShippingMethod
from shuup.core.order_creator import OrderSource, SourceLine
from shuup.core.order_creator._source import LineSource
from shuup.front.basket.storage import BasketCompatibilityError, get_storage
from shuup.utils.numbers import parse_decimal_string
from shuup.utils.objects import compare_partial_dicts


class BasketLine(SourceLine):
    def __init__(self, source=None, **kwargs):
        self.__in_init = True
        super(BasketLine, self).__init__(source, **kwargs)
        self.__in_init = False

    @property
    def shop_product(self):
        """
        ShopProduct object of this line.

        :rtype: shuup.core.models.ShopProduct
        """
        return self.product.get_shop_instance(self.shop)

    def cache_info(self, request):
        product = self.product
        # TODO: ensure shop identity?
        price_info = product.get_price_info(request, quantity=self.quantity)
        self.base_unit_price = price_info.base_unit_price
        self.discount_amount = price_info.discount_amount
        assert self.price == price_info.price
        self.net_weight = product.net_weight
        self.gross_weight = product.gross_weight
        self.shipping_mode = product.shipping_mode
        self.sku = product.sku
        self.text = product.safe_translation_getter("name", any_language=True)

    @property
    def type(self):
        if self.product:
            return OrderLineType.PRODUCT
        else:
            return (self.__dict__.get("type") or OrderLineType.OTHER)

    @type.setter
    def type(self, type):
        if self.__in_init:
            self.__dict__["type"] = type
            return

        if self.product and type != OrderLineType.PRODUCT:
            raise ValueError("Can not set a line type for a basket line when it has a product set")
        if type not in OrderLineType.as_dict():
            raise ValueError("Invalid basket line type. Only values of OrderLineType are allowed.")
        self.__dict__["type"] = type

    def set_quantity(self, quantity):
        cls = Decimal if self.product.sales_unit.allow_fractions else int
        self.quantity = cls(max(0, quantity))

    @property
    def can_delete(self):
        return (self.type == OrderLineType.PRODUCT and self.line_source != LineSource.DISCOUNT_MODULE)

    @property
    def can_change_quantity(self):
        return (self.type == OrderLineType.PRODUCT and self.line_source != LineSource.DISCOUNT_MODULE)


class BaseBasket(OrderSource):
    def __init__(self, request, basket_name="basket"):
        super(BaseBasket, self).__init__(request.shop)
        self.basket_name = basket_name
        self.request = request
        if request:
            self.ip_address = request.META.get("REMOTE_ADDR")
        self.storage = get_storage()
        self._data = None
        self.dirty = False
        self.customer = getattr(request, "customer", None)
        self.orderer = getattr(request, "person", None)
        self.creator = getattr(request, "user", None)

    def _load(self):
        """
        Get the currently persisted data for this basket.

        This will only access the storage once per request in usual
        circumstances.

        :return: Data dict.
        :rtype: dict
        """
        if self._data is None:
            try:
                self._data = self.storage.load(basket=self)
            except BasketCompatibilityError as error:
                msg = _("Basket loading failed: Incompatible basket (%s)")
                messages.error(self.request, msg % error)
                self.storage.delete(basket=self)
                self._data = self.storage.load(basket=self)
            self.dirty = False
        return self._data

    def save(self):
        """
        Persist any changes made into the basket to storage.

        One does not usually need to directly call this;
        :obj:`~shuup.front.middleware.ShuupFrontMiddleware` will usually
        take care of it.
        """
        self.clean_empty_lines()
        self.storage.save(basket=self, data=self._data)
        self.dirty = False

    def delete(self):
        """
        Clear and delete the basket data.
        """
        self.storage.delete(basket=self)
        self.uncache()
        self._data = None
        self.dirty = False

    def finalize(self):
        """
        Mark the basket as "completed" (i.e. an order is created/a conversion made).

        This will also clear the basket's data.
        """
        self.storage.finalize(basket=self)
        self.uncache()
        self._data = None
        self.dirty = False

    def clear_all(self):
        """
        Clear all data for this basket.
        """
        self._data = {}
        self.uncache()
        self.dirty = True

    @property
    def _data_lines(self):
        """
        Get the line data (list of dicts).

        If the list is edited, it must be re-assigned
        to ``self._data_lines`` to ensure the `dirty`
        flag gets set.

        :return: List of data dicts
        :rtype: list[dict]
        """
        return self._load().setdefault("lines", [])

    @_data_lines.setter
    def _data_lines(self, new_lines):
        """
        Set the line data (list of dicts).

        Note that this assignment must be made instead
        of editing `_data_lines` in-place to ensure
        the `dirty` bit gets set.

        :param new_lines: New list of lines.
        :type new_lines: list[dict]
        """
        self._load()["lines"] = new_lines
        self.dirty = True
        self.uncache()

    def add_line(self, **kwargs):
        line = self.create_line(**kwargs)
        self._data_lines = self._data_lines + [line.to_dict()]
        return line

    def create_line(self, **kwargs):
        return BasketLine(source=self, **kwargs)

    @property
    def _codes(self):
        return self._load().setdefault("codes", [])

    @_codes.setter
    def _codes(self, value):
        if hasattr(self, "_data"):  # Check that we're initialized
            self._load()["codes"] = value

    def add_code(self, code):
        modified = super(BaseBasket, self).add_code(code)
        self.dirty = bool(self.dirty or modified)
        return modified

    def clear_codes(self):
        modified = super(BaseBasket, self).clear_codes()
        self.dirty = bool(self.dirty or modified)
        return modified

    def remove_code(self, code):
        modified = super(BaseBasket, self).remove_code(code)
        self.dirty = bool(self.dirty or modified)
        return modified

    def get_lines(self):
        return [BasketLine.from_dict(self, line) for line in self._data_lines]

    def _initialize_product_line_data(self, product, supplier, shop, quantity=0):
        if product.variation_children.count():
            raise ValueError("Attempting to add variation parent to basket")

        return {
            # TODO: FIXME: Make sure line_id's are unique (not random)
            "line_id": str(random.randint(0, 0x7FFFFFFF)),
            "product": product,
            "supplier": supplier,
            "shop": shop,
            "quantity": parse_decimal_string(quantity),
        }

    def clean_empty_lines(self):
        new_lines = [l for l in self._data_lines if l["quantity"] > 0]
        if len(new_lines) != len(self._data_lines):
            self._data_lines = new_lines

    def _compare_line_for_addition(self, current_line_data, product, supplier, shop, extra):
        """
        Compare raw line data for coalescing.

        That is, figure out whether the given raw line data is similar enough to product_id
        and extra to coalesce quantity additions.

        This is nice to override in a project-specific basket class.

        :type current_line_data: dict
        :type product: int
        :type extra: dict
        :return:
        """
        if current_line_data.get("product_id") != product.id:
            return False
        if current_line_data.get("supplier_id") != supplier.id:
            return False
        if current_line_data.get("shop_id") != shop.id:
            return False

        if isinstance(extra, dict):  # We have extra data, so compare it to that in this line
            if not compare_partial_dicts(extra, current_line_data):  # Extra data not similar? Okay then. :(
                return False
        return True

    def _find_product_line_data(self, product, supplier, shop, extra):
        """
        Find the underlying basket data dict for a given product and line-specific extra data.
        This uses _compare_line_for_addition internally, which is nice to override in a project-specific basket class.

        :param product: Product object
        :param extra: optional dict of extra data
        :return: dict of line or None
        """
        for line_data in self._data_lines:
            if self._compare_line_for_addition(line_data, product, supplier, shop, extra):
                return line_data

    def _add_or_replace_line(self, data_line):
        self.dirty = True
        if isinstance(data_line, SourceLine):
            data_line = data_line.to_dict()
        assert isinstance(data_line, dict)
        line_ids = [x["line_id"] for x in self._data_lines]
        try:
            index = line_ids.index(data_line["line_id"])
        except ValueError:
            index = len(line_ids)
        self.delete_line(data_line["line_id"])
        self._data_lines.insert(index, data_line)
        self._data_lines = list(self._data_lines)  # This will set the dirty bit and call uncache.

    def add_product(self, supplier, shop, product, quantity, force_new_line=False, extra=None, parent_line=None):
        if not extra:
            extra = {}

        if quantity <= 0:
            raise ValueError("Invalid quantity!")

        data = None
        if not force_new_line:
            data = self._find_product_line_data(product=product, supplier=supplier, shop=shop, extra=extra)

        if not data:
            data = self._initialize_product_line_data(product=product, supplier=supplier, shop=shop)

        if parent_line:
            data["parent_line_id"] = parent_line.line_id

        new_quantity = max(0, data["quantity"] + Decimal(quantity))

        return self.update_line(data, quantity=new_quantity, **extra)

    def update_line(self, data_line, **kwargs):
        line = BasketLine.from_dict(self, data_line)
        new_quantity = kwargs.pop("quantity", None)
        if new_quantity is not None:
            line.set_quantity(new_quantity)
        line.update(**kwargs)
        line.cache_info(self.request)
        self._add_or_replace_line(line)
        return line

    def add_product_with_child_product(self, supplier, shop, product, child_product, quantity):
        parent_line = self.add_product(
            supplier=supplier,
            shop=shop,
            product=product,
            quantity=quantity,
            force_new_line=True
        )
        child_line = self.add_product(
            supplier=supplier,
            shop=shop,
            product=child_product,
            quantity=quantity,
            parent_line=parent_line,
            force_new_line=True
        )
        return (parent_line, child_line)

    def delete_line(self, line_id):
        line = self.find_line_by_line_id(line_id)
        if line:
            line["quantity"] = 0
            for subline in self.find_lines_by_parent_line_id(line_id):
                subline["quantity"] = 0
            self.uncache()
            self.clean_empty_lines()
            return True
        return False

    def find_line_by_line_id(self, line_id):
        for line in self._data_lines:
            if six.text_type(line.get("line_id")) == six.text_type(line_id):
                return line
        return None

    def find_lines_by_parent_line_id(self, parent_line_id):
        for line in self._data_lines:
            if six.text_type(line.get("parent_line_id")) == six.text_type(parent_line_id):
                yield line

    def _get_orderable(self):
        return (sum(l.quantity for l in self.get_lines()) > 0)

    orderable = property(_get_orderable)

    def get_validation_errors(self):
        for error in super(BaseBasket, self).get_validation_errors():
            yield error

        shipping_methods = self.get_available_shipping_methods()
        payment_methods = self.get_available_payment_methods()

        advice = _(
            "Try to remove some products from the basket "
            "and order them separately.")

        if self.has_shippable_lines() and not shipping_methods:
            msg = _("Products in basket cannot be shipped together. %s")
            yield ValidationError(msg % advice, code="no_common_shipping")

        if not payment_methods:
            msg = _("Products in basket have no common payment method. %s")
            yield ValidationError(msg % advice, code="no_common_payment")

    def get_product_ids_and_quantities(self):
        q_counter = Counter()
        for line in self.get_lines():
            product_id = line.product.id if line.product else None
            if product_id:
                q_counter[product_id] += line.quantity

        return dict(q_counter)

    def get_available_shipping_methods(self):
        """
        Get available shipping methods.

        :rtype: list[ShippingMethod]
        """
        return [
            m for m
            in ShippingMethod.objects.available(shop=self.shop, products=self.product_ids)
            if m.is_available_for(self)
        ]

    def get_available_payment_methods(self):
        """
        Get available payment methods.

        :rtype: list[PaymentMethod]
        """
        return [
            m for m
            in PaymentMethod.objects.available(shop=self.shop, products=self.product_ids)
            if m.is_available_for(self)
        ]
