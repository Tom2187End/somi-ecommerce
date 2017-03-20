# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField

from shuup.core.excs import (
    ProductNotOrderableProblem, ProductNotVisibleProblem
)
from shuup.core.fields import MoneyValueField, QuantityField, UnsavedForeignKey
from shuup.core.signals import get_orderability_errors, get_visibility_errors
from shuup.core.utils import context_cache
from shuup.utils.analog import define_log_model
from shuup.utils.properties import MoneyPropped, PriceProperty

from ._product_media import ProductMediaKind
from ._products import ProductMode, ProductVisibility, StockBehavior
from ._units import DisplayUnit, PiecesSalesUnit, UnitInterface

mark_safe_lazy = lazy(mark_safe, six.text_type)


class ShopProductVisibility(Enum):
    NOT_VISIBLE = 0
    SEARCHABLE = 1
    LISTED = 2
    ALWAYS_VISIBLE = 3

    class Labels:
        NOT_VISIBLE = _("not visible")
        SEARCHABLE = _("searchable")
        LISTED = _("listed")
        ALWAYS_VISIBLE = _("always visible")


class ShopProduct(MoneyPropped, models.Model):
    shop = models.ForeignKey("Shop", related_name="shop_products", on_delete=models.CASCADE, verbose_name=_("shop"))
    product = UnsavedForeignKey(
        "Product", related_name="shop_products", on_delete=models.CASCADE, verbose_name=_("product"))
    suppliers = models.ManyToManyField(
        "Supplier", related_name="shop_products", blank=True, verbose_name=_("suppliers"), help_text=_(
            "List your suppliers here. Suppliers can be found in Product Settings - Suppliers."
        )
    )

    visibility = EnumIntegerField(
        ShopProductVisibility,
        default=ShopProductVisibility.ALWAYS_VISIBLE,
        db_index=True,
        verbose_name=_("visibility"),
        help_text=mark_safe_lazy(_(
            "Select if you want your product to be seen and found by customers. "
            "<p>Not visible: Product will not be shown in your store front or found in search.</p>"
            "<p>Searchable: Product will be shown in search but not listed on any category page.</p>"
            "<p>Listed: Product will be shown on category pages but not shown in search results.</p>"
            "<p>Always Visible: Product will be shown in your store front and found in search.</p>"
        ))
    )
    purchasable = models.BooleanField(default=True, db_index=True, verbose_name=_("purchasable"))
    visibility_limit = EnumIntegerField(
        ProductVisibility, db_index=True, default=ProductVisibility.VISIBLE_TO_ALL,
        verbose_name=_('visibility limitations'), help_text=_(
            "Select whether you want your product to have special limitations on its visibility in your store. "
            "You can make products visible to all, visible to only logged in users, or visible only to certain "
            "customer groups."
        )
    )
    visibility_groups = models.ManyToManyField(
        "ContactGroup", related_name='visible_products', verbose_name=_('visible for groups'), blank=True, help_text=_(
            u"Select the groups you would like to make your product visible for. "
            u"These groups are defined in Contacts Settings - Contact Groups."
        )
    )
    backorder_maximum = QuantityField(
        default=0, blank=True, null=True, verbose_name=_('backorder maximum'), help_text=_(
            "The number of units that can be purchased after the product is out of stock. "
            "Set to blank for product to be purchasable without limits."
        ))
    purchase_multiple = QuantityField(default=0, verbose_name=_('purchase multiple'), help_text=_(
            "Set this if the product needs to be purchased in multiples. "
            "For example, if the purchase multiple is set to 2, then customers are required to order the product "
            "in multiples of 2."
        )
    )
    minimum_purchase_quantity = QuantityField(default=1, verbose_name=_('minimum purchase'), help_text=_(
            "Set a minimum number of products needed to be ordered for the purchase. "
            "This is useful for setting bulk orders and B2B purchases."
        )
    )
    limit_shipping_methods = models.BooleanField(
        default=False, verbose_name=_("limited for shipping methods"), help_text=_(
            "Check this if you want to limit your product to use only select payment methods. "
            "You can select the payment method(s) in the field below."
        )
    )
    limit_payment_methods = models.BooleanField(
        default=False, verbose_name=_("limited for payment methods"), help_text=_(
            "Check this if you want to limit your product to use only select payment methods. "
            "You can select the payment method(s) in the field below."
        )
    )
    shipping_methods = models.ManyToManyField(
        "ShippingMethod", related_name='shipping_products', verbose_name=_('shipping methods'), blank=True, help_text=_(
            "Select the shipping methods you would like to limit the product to using. "
            "These are defined in Settings - Shipping Methods."
        )
    )
    payment_methods = models.ManyToManyField(
        "PaymentMethod", related_name='payment_products', verbose_name=_('payment methods'), blank=True, help_text=_(
            "Select the payment methods you would like to limit the product to using. "
            "These are defined in Settings - Payment Methods."
        )
    )
    primary_category = models.ForeignKey(
        "Category", related_name='primary_shop_products', verbose_name=_('primary category'), blank=True, null=True,
        on_delete=models.PROTECT, help_text=_(
            "Choose the primary category for your product. "
            "This will be the main category for classification in the system. "
            "Your product can be found under this category in your store. "
            "Categories are defined in Products Settings - Categories."
        )
    )
    categories = models.ManyToManyField(
        "Category", related_name='shop_products', verbose_name=_('categories'), blank=True, help_text=_(
            "Add secondary categories for your product. "
            "These are other categories that your product fits under and that it can be found by in your store."
        )
    )
    shop_primary_image = models.ForeignKey(
        "ProductMedia", null=True, blank=True,
        related_name="primary_image_for_shop_products", on_delete=models.SET_NULL,
        verbose_name=_("primary image"), help_text=_(
            "Click this to set this image as the primary display image for your product."
        )
    )

    # the default price of this product in the shop
    default_price = PriceProperty('default_price_value', 'shop.currency', 'shop.prices_include_tax')
    default_price_value = MoneyValueField(verbose_name=_("default price"), null=True, blank=True, help_text=_(
            "This is the default individual base unit (or multi-pack) price of the product. "
            "All discounts or coupons will be based off of this price."
        )
    )

    minimum_price = PriceProperty('minimum_price_value', 'shop.currency', 'shop.prices_include_tax')
    minimum_price_value = MoneyValueField(verbose_name=_("minimum price"), null=True, blank=True, help_text=_(
            "This is the default price that the product cannot go under in your store, "
            "despite coupons or discounts being applied. "
            "This is useful to make sure your product price stays above cost."
        )
    )

    display_unit = models.ForeignKey(
        DisplayUnit, null=True, blank=True,
        verbose_name=_("display unit"),
        help_text=_("Unit for displaying quantities of this product"))

    class Meta:
        unique_together = (("shop", "product",),)

    def save(self, *args, **kwargs):
        self.clean()
        super(ShopProduct, self).save(*args, **kwargs)
        for supplier in self.suppliers.all():
            supplier.module.update_stock(product_id=self.product.id)

    def clean(self):
        super(ShopProduct, self).clean()
        if self.display_unit:
            if self.display_unit.internal_unit != self.product.sales_unit:
                raise ValidationError({'display_unit': _(
                    "Invalid display unit: Internal unit of "
                    "the selected display unit does not match "
                    "with the sales unit of the product")})

    def is_list_visible(self):
        """
        Return True if this product should be visible in listings in general,
        without taking into account any other visibility limitations.
        :rtype: bool
        """
        if self.product.deleted:
            return False
        if not self.listed:
            return False
        if self.product.is_variation_child():
            return False
        return True

    @property
    def primary_image(self):
        if self.shop_primary_image_id:
            return self.shop_primary_image
        else:
            return self.product.primary_image

    @property
    def searchable(self):
        return self.visibility in (ShopProductVisibility.SEARCHABLE, ShopProductVisibility.ALWAYS_VISIBLE)

    @property
    def listed(self):
        return self.visibility in (ShopProductVisibility.LISTED, ShopProductVisibility.ALWAYS_VISIBLE)

    @property
    def visible(self):
        return not (self.visibility == ShopProductVisibility.NOT_VISIBLE)

    @property
    def public_primary_image(self):
        primary_image = self.primary_image
        return primary_image if primary_image and primary_image.public else None

    def get_visibility_errors(self, customer):
        if self.product.deleted:
            yield ValidationError(_('This product has been deleted.'), code="product_deleted")

        if customer and customer.is_all_seeing:  # None of the further conditions matter for omniscient customers.
            return

        if not self.visible:
            yield ValidationError(_('This product is not visible.'), code="product_not_visible")

        is_logged_in = (bool(customer) and not customer.is_anonymous)

        if not is_logged_in and self.visibility_limit != ProductVisibility.VISIBLE_TO_ALL:
            yield ValidationError(
                _('The Product is invisible to users not logged in.'),
                code="product_not_visible_to_anonymous")

        if is_logged_in and self.visibility_limit == ProductVisibility.VISIBLE_TO_GROUPS:
            # TODO: Optimization
            user_groups = set(customer.groups.all().values_list("pk", flat=True))
            my_groups = set(self.visibility_groups.values_list("pk", flat=True))
            if not bool(user_groups & my_groups):
                yield ValidationError(
                    _('This product is not visible to your group.'),
                    code="product_not_visible_to_group"
                )

        for receiver, response in get_visibility_errors.send(ShopProduct, shop_product=self, customer=customer):
            for error in response:
                yield error

    # TODO: Refactor get_orderability_errors, it's too complex
    def get_orderability_errors(  # noqa (C901)
            self, supplier, quantity, customer, ignore_minimum=False):
        """
        Yield ValidationErrors that would cause this product to not be orderable.

        :param supplier: Supplier to order this product from. May be None.
        :type supplier: shuup.core.models.Supplier
        :param quantity: Quantity to order.
        :type quantity: int|Decimal
        :param customer: Customer contact.
        :type customer: shuup.core.models.Contact
        :param ignore_minimum: Ignore any limitations caused by quantity minimums.
        :type ignore_minimum: bool
        :return: Iterable[ValidationError]
        """
        for error in self.get_visibility_errors(customer):
            yield error

        if supplier is None and not self.suppliers.exists():
            # `ShopProduct` must have at least one `Supplier`.
            # If supplier is not given and the `ShopProduct` itself
            # doesn't have suppliers we cannot sell this product.
            yield ValidationError(
                _('The product has no supplier.'),
                code="no_supplier"
            )

        if not ignore_minimum and quantity < self.minimum_purchase_quantity:
            yield ValidationError(
                _('The purchase quantity needs to be at least %d for this product.') % self.minimum_purchase_quantity,
                code="purchase_quantity_not_met"
            )

        if supplier and not self.suppliers.filter(pk=supplier.pk).exists():
            yield ValidationError(
                _('The product is not supplied by %s.') % supplier,
                code="invalid_supplier"
            )

        if self.product.mode == ProductMode.SIMPLE_VARIATION_PARENT:
            sellable = False
            for child_product in self.product.variation_children.all():
                child_shop_product = child_product.get_shop_instance(self.shop)
                if child_shop_product.is_orderable(
                        supplier=supplier,
                        customer=customer,
                        quantity=child_shop_product.minimum_purchase_quantity,
                        allow_cache=False
                ):
                    sellable = True
                    break
            if not sellable:
                yield ValidationError(_("Product has no sellable children"), code="no_sellable_children")
        elif self.product.mode == ProductMode.VARIABLE_VARIATION_PARENT:
            from shuup.core.models import ProductVariationResult
            sellable = False
            for combo in self.product.get_all_available_combinations():
                res = ProductVariationResult.resolve(self.product, combo["variable_to_value"])
                if not res:
                    continue
                child_shop_product = res.get_shop_instance(self.shop)
                if child_shop_product.is_orderable(
                        supplier=supplier,
                        customer=customer,
                        quantity=child_shop_product.minimum_purchase_quantity,
                        allow_cache=False
                ):
                    sellable = True
                    break
            if not sellable:
                yield ValidationError(_("Product has no sellable children"), code="no_sellable_children")

        if self.product.is_package_parent():
            for child_product, child_quantity in six.iteritems(self.product.get_package_child_to_quantity_map()):
                try:
                    child_shop_product = child_product.get_shop_instance(shop=self.shop, allow_cache=False)
                except ShopProduct.DoesNotExist:
                    yield ValidationError("%s: Not available in %s" % (child_product, self.shop), code="invalid_shop")
                else:
                    for error in child_shop_product.get_orderability_errors(
                            supplier=supplier,
                            quantity=(quantity * child_quantity),
                            customer=customer,
                            ignore_minimum=ignore_minimum
                    ):
                        message = getattr(error, "message", "")
                        code = getattr(error, "code", None)
                        yield ValidationError("%s: %s" % (child_product, message), code=code)

        if supplier and self.product.stock_behavior == StockBehavior.STOCKED:
            for error in supplier.get_orderability_errors(self, quantity, customer=customer):
                yield error

        purchase_multiple = self.purchase_multiple
        if quantity > 0 and purchase_multiple > 1 and (quantity % purchase_multiple) != 0:
            p = (quantity // purchase_multiple)
            smaller_p = max(purchase_multiple, p * purchase_multiple)
            larger_p = max(purchase_multiple, (p + 1) * purchase_multiple)
            if larger_p == smaller_p:
                message = _('The product can only be ordered in multiples of %(package_size)s, '
                            'for example %(smaller_p)s %(unit)s.') % {
                    "package_size": purchase_multiple,
                    "smaller_p": smaller_p,
                    "unit": self.product.sales_unit,
                }
            else:
                message = _('The product can only be ordered in multiples of %(package_size)s, '
                            'for example %(smaller_p)s or %(larger_p)s %(unit)s.') % {
                    "package_size": purchase_multiple,
                    "smaller_p": smaller_p,
                    "larger_p": larger_p,
                    "unit": self.product.sales_unit,
                }
            yield ValidationError(message, code="invalid_purchase_multiple")

        for receiver, response in get_orderability_errors.send(
            ShopProduct, shop_product=self, customer=customer, supplier=supplier, quantity=quantity
        ):
            for error in response:
                yield error

    def raise_if_not_orderable(self, supplier, customer, quantity, ignore_minimum=False):
        for message in self.get_orderability_errors(
            supplier=supplier, quantity=quantity, customer=customer, ignore_minimum=ignore_minimum
        ):
            raise ProductNotOrderableProblem(message.args[0])

    def raise_if_not_visible(self, customer):
        for message in self.get_visibility_errors(customer=customer):
            raise ProductNotVisibleProblem(message.args[0])

    def is_orderable(self, supplier, customer, quantity, allow_cache=True):
        key, val = context_cache.get_cached_value(
            identifier="is_orderable", item=self, context={"customer": customer},
            supplier=supplier, quantity=quantity, allow_cache=allow_cache)
        if customer and val is not None:
            return val

        if not supplier:
            supplier = self.suppliers.first()  # TODO: Allow multiple suppliers
        for message in self.get_orderability_errors(supplier=supplier, quantity=quantity, customer=customer):
            if customer:
                context_cache.set_cached_value(key, False)
            return False

        if customer:
            context_cache.set_cached_value(key, True)
        return True

    def is_visible(self, customer):
        for message in self.get_visibility_errors(customer=customer):
            return False
        return True

    @property
    def quantity_step(self):
        """
        Quantity step for purchasing this product.

        :rtype: decimal.Decimal

        Example:
            <input type="number" step="{{ shop_product.quantity_step }}">
        """
        step = self.purchase_multiple or self._sales_unit.quantity_step
        return self._sales_unit.round(step)

    @property
    def rounded_minimum_purchase_quantity(self):
        """
        The minimum purchase quantity, rounded to the sales unit's precision.

        :rtype: decimal.Decimal

        Example:
            <input type="number"
                min="{{ shop_product.rounded_minimum_purchase_quantity }}"
                value="{{ shop_product.rounded_minimum_purchase_quantity }}">

        """
        return self._sales_unit.round(self.minimum_purchase_quantity)

    @property
    def display_quantity_step(self):
        """
        Quantity step of this shop product in the display unit.

        Note: This can never be smaller than the display precision.
        """
        return max(
            self.unit.to_display(self.quantity_step),
            self.unit.display_precision)

    @property
    def display_quantity_minimum(self):
        """
        Quantity minimum of this shop product in the display unit.

        Note: This can never be smaller than the display precision.
        """
        return max(
            self.unit.to_display(self.minimum_purchase_quantity),
            self.unit.display_precision)

    @property
    def unit(self):
        """
        Unit of this product.

        :rtype: shuup.core.models.UnitInterface
        """
        return UnitInterface(self._sales_unit, self.display_unit)

    @property
    def _sales_unit(self):
        return self.product.sales_unit or PiecesSalesUnit()

    @property
    def images(self):
        return self.product.media.filter(shops=self.shop, kind=ProductMediaKind.IMAGE).order_by("ordering")

    @property
    def public_images(self):
        return self.images.filter(public=True)


ShopProductLogEntry = define_log_model(ShopProduct)
