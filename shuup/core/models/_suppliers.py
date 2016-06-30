# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from jsonfield import JSONField

from shuup.core.fields import InternalIdentifierField
from shuup.core.modules import ModuleInterface

from ._base import ShuupModel


class SupplierType(Enum):
    INTERNAL = 1
    EXTERNAL = 2

    class Labels:
        INTERNAL = _('internal')
        EXTERNAL = _('external')


@python_2_unicode_compatible
class Supplier(ModuleInterface, ShuupModel):
    default_module_spec = "shuup.core.suppliers:BaseSupplierModule"
    module_provides_key = "supplier_module"

    identifier = InternalIdentifierField(unique=True)
    name = models.CharField(verbose_name=_("name"), max_length=64)
    type = EnumIntegerField(SupplierType, verbose_name=_("supplier type"), default=SupplierType.INTERNAL)
    stock_managed = models.BooleanField(verbose_name=_("stock managed"), default=False)
    module_identifier = models.CharField(max_length=64, blank=True, verbose_name=_('module'))
    module_data = JSONField(blank=True, null=True, verbose_name=_("module data"))

    def __str__(self):
        return self.name

    def get_orderability_errors(self, shop_product, quantity, customer):
        """
        :param shop_product: Shop Product
        :type shop_product: shuup.core.models.ShopProduct
        :param quantity: Quantity to order
        :type quantity: decimal.Decimal
        :param contect: Ordering contact.
        :type contect: shuup.core.models.Contact
        :rtype: iterable[ValidationError]
        """
        return self.module.get_orderability_errors(shop_product=shop_product, quantity=quantity, customer=customer)

    def get_stock_statuses(self, product_ids):
        """
        :param product_ids: Iterable of product IDs
        :return: Dict of {product_id: ProductStockStatus}
        :rtype: dict[int, shuup.core.stocks.ProductStockStatus]
        """
        return self.module.get_stock_statuses(product_ids)

    def get_stock_status(self, product_id):
        """
        :param product_id: Product ID
        :type product_id: int
        :rtype: shuup.core.stocks.ProductStockStatus
        """
        return self.module.get_stock_status(product_id)

    def get_suppliable_products(self, shop, customer):
        """
        :param shop: Shop to check for suppliability
        :type shop: shuup.core.models.Shop
        :param customer: Customer contact to check for suppliability
        :type customer: shuup.core.models.Contact
        :rtype: list[int]
        """
        return [
            shop_product.pk
            for shop_product
            in self.shop_products.filter(shop=shop)
            if shop_product.is_orderable(self, customer, shop_product.minimum_purchase_quantity)
        ]

    def adjust_stock(self, product_id, delta, created_by=None):
        return self.module.adjust_stock(product_id, delta, created_by=created_by)

    def update_stock(self, product_id):
        return self.module.update_stock(product_id)

    def update_stocks(self, product_ids):
        return self.module.update_stocks(product_ids)
