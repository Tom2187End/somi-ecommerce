# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from filer.fields.image import FilerImageField
from jsonfield import JSONField
from parler.models import TranslatedFields

from shuup.core.fields import CurrencyField, InternalIdentifierField
from shuup.core.pricing import TaxfulPrice, TaxlessPrice
from shuup.utils.analog import define_log_model

from ._base import ChangeProtected, TranslatableShuupModel
from ._orders import Order


def _get_default_currency():
    return settings.SHUUP_HOME_CURRENCY


class ShopStatus(Enum):
    DISABLED = 0
    ENABLED = 1

    class Labels:
        DISABLED = _('disabled')
        ENABLED = _('enabled')


@python_2_unicode_compatible
class Shop(ChangeProtected, TranslatableShuupModel):
    protected_fields = ["currency", "prices_include_tax"]
    change_protect_message = _("The following fields cannot be changed since there are existing orders for this shop")

    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_('created on'))
    modified_on = models.DateTimeField(auto_now=True, editable=False, db_index=True, verbose_name=_('modified on'))
    identifier = InternalIdentifierField(unique=True, max_length=128)
    domain = models.CharField(max_length=128, blank=True, null=True, unique=True, verbose_name=_("domain"), help_text=_(
        "Your shop domain name. Use this field to configure the URL that is used to visit your site. "
        "Note: this requires additional configuration through your internet domain registrar."
    ))
    status = EnumIntegerField(ShopStatus, default=ShopStatus.DISABLED, verbose_name=_("status"), help_text=_(
        "Your shop status. Disable your shop if it is no longer in use."
    ))
    owner = models.ForeignKey("Contact", blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("contact"))
    options = JSONField(blank=True, null=True, verbose_name=_("options"))
    currency = CurrencyField(default=_get_default_currency, verbose_name=_("currency"), help_text=_(
        "The primary shop currency. This is the currency used when selling your products."
    ))
    prices_include_tax = models.BooleanField(default=True, verbose_name=_("prices include tax"), help_text=_(
        "This option defines whether product prices entered in admin include taxes. "
        "Note this behavior can be overridden with contact group pricing."
    ))
    logo = FilerImageField(
        verbose_name=_("logo"), blank=True, null=True, on_delete=models.SET_NULL,
        help_text=_("Shop logo. Will be shown at theme."), related_name="shop_logos")

    favicon = FilerImageField(
        verbose_name=_("favicon"), blank=True, null=True, on_delete=models.SET_NULL,
        help_text=_("Shop favicon. Will be shown next to the address on browser."), related_name="shop_favicons")

    maintenance_mode = models.BooleanField(verbose_name=_("maintenance mode"), default=False, help_text=_(
        "Check this if you would like to make your shop temporarily unavailable while you do some shop maintenance."
    ))
    contact_address = models.ForeignKey(
        "MutableAddress", verbose_name=_("contact address"), blank=True, null=True, on_delete=models.SET_NULL)
    staff_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="+", verbose_name=_('staff members'))

    translations = TranslatedFields(
        name=models.CharField(max_length=64, verbose_name=_("name"), help_text=_(
            "The shop name. This name is displayed throughout admin."
        )),
        public_name=models.CharField(max_length=64, verbose_name=_("public name"), help_text=_(
            "The public shop name. This name is displayed in the store front and in any customer email correspondence."
        )),
        maintenance_message=models.CharField(
            max_length=300, blank=True, verbose_name=_("maintenance message"), help_text=_(
                "The message to display to customers while your shop is in maintenance mode."
            )
        )
    )

    def __str__(self):
        return self.safe_translation_getter("name", default="Shop %d" % self.pk)

    def create_price(self, value):
        """
        Create a price with given value and settings of this shop.

        Takes the ``prices_include_tax`` and ``currency`` settings of
        this Shop into account.

        :type value: decimal.Decimal|int|str
        :rtype: shuup.core.pricing.Price
        """
        if self.prices_include_tax:
            return TaxfulPrice(value, self.currency)
        else:
            return TaxlessPrice(value, self.currency)

    def _are_changes_protected(self):
        return Order.objects.filter(shop=self).exists()


ShopLogEntry = define_log_model(Shop)
