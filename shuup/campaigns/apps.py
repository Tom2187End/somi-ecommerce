# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.db.models.signals import m2m_changed, post_save

from shuup.apps import AppConfig
from shuup.campaigns.models.catalog_filters import (
    CategoryFilter, ProductFilter
)
from shuup.campaigns.models.context_conditions import (
    ContactCondition, ContactGroupCondition
)
from shuup.campaigns.signal_handlers import (
    invalidate_context_condition_cache, invalidate_context_filter_cache,
    update_customers_groups
)
from shuup.core.models import ContactGroup, Payment, ShopProduct


class CampaignAppConfig(AppConfig):
    name = "shuup.campaigns"
    verbose_name = "Shuup Campaigns"
    label = "campaigns"
    provides = {
        "admin_contact_group_form_part": [
            "shuup.campaigns.admin_module.form_parts:SalesRangesFormPart"
        ],
        "discount_module": [
            "shuup.campaigns.modules:CatalogCampaignModule"
        ],
        "order_source_modifier_module": [
            "shuup.campaigns.modules:BasketCampaignModule"
        ],
        "admin_module": [
            "shuup.campaigns.admin_module:CampaignAdminModule",
        ],
        "admin_product_section": [
            "shuup.campaigns.admin_module.sections:ProductCampaignsSection"
        ],
        "campaign_basket_condition": [
            "shuup.campaigns.admin_module.forms:BasketTotalProductAmountConditionForm",
            "shuup.campaigns.admin_module.forms:BasketTotalAmountConditionForm",
            "shuup.campaigns.admin_module.forms:BasketMaxTotalProductAmountConditionForm",
            "shuup.campaigns.admin_module.forms:BasketMaxTotalAmountConditionForm",
            "shuup.campaigns.admin_module.forms:ProductsInBasketConditionForm",
            "shuup.campaigns.admin_module.forms:ContactGroupBasketConditionForm",
            "shuup.campaigns.admin_module.forms:ContactBasketConditionForm",
            "shuup.campaigns.admin_module.forms:CategoryProductsBasketConditionForm"
        ],
        "campaign_basket_discount_effect_form": [
            "shuup.campaigns.admin_module.forms:BasketDiscountAmountForm",
            "shuup.campaigns.admin_module.forms:BasketDiscountPercentageForm"
        ],
        "campaign_basket_line_effect_form": [
            "shuup.campaigns.admin_module.forms:FreeProductLineForm",
            "shuup.campaigns.admin_module.forms:DiscountFromProductForm",
            "shuup.campaigns.admin_module.forms:DiscountFromCategoryProductsForm",
        ],
        "campaign_context_condition": [
            "shuup.campaigns.admin_module.forms:ContactGroupConditionForm",
            "shuup.campaigns.admin_module.forms:ContactConditionForm",
        ],
        "campaign_catalog_filter": [
            "shuup.campaigns.admin_module.forms:ProductTypeFilterForm",
            "shuup.campaigns.admin_module.forms:ProductFilterForm",
            "shuup.campaigns.admin_module.forms:CategoryFilterForm"
        ],
        "campaign_product_discount_effect_form": [
            "shuup.campaigns.admin_module.forms:ProductDiscountAmountForm",
            "shuup.campaigns.admin_module.forms:ProductDiscountPercentageForm",
        ],
    }

    def ready(self):
        post_save.connect(
            update_customers_groups,
            sender=Payment,
            dispatch_uid="contact_group_sales:update_customers_groups"
        )

        # Invalidate context condition caches
        m2m_changed.connect(
            invalidate_context_condition_cache,
            sender=ContactGroup.members.through,
            dispatch_uid="campaigns:invalidate_caches_for_contact_group_m2m_change"
        )
        m2m_changed.connect(
            invalidate_context_condition_cache,
            sender=ContactCondition.contacts.through,
            dispatch_uid="campaigns:invalidate_caches_for_contacts_condition_m2m_change"
        )
        m2m_changed.connect(
            invalidate_context_condition_cache,
            sender=ContactGroupCondition.contact_groups.through,
            dispatch_uid="campaigns:invalidate_caches_for_contact_group_condition_m2m_change"
        )

        # Invalidate context filter caches
        m2m_changed.connect(
            invalidate_context_filter_cache,
            sender=CategoryFilter.categories.through,
            dispatch_uid="campaigns:invalidate_caches_for_category_filter_m2m_change"
        )
        m2m_changed.connect(
            invalidate_context_filter_cache,
            sender=ProductFilter.products.through,
            dispatch_uid="campaigns:invalidate_caches_for_product_filter_m2m_change"
        )
        post_save.connect(
            invalidate_context_filter_cache,
            sender=ShopProduct,
            dispatch_uid="campaigns:invalidate_caches_for_shop_product_save"
        )
        m2m_changed.connect(
            invalidate_context_filter_cache,
            sender=ShopProduct.categories.through,
            dispatch_uid="campaigns:invalidate_caches_for_shop_product_m2m_change"
        )
