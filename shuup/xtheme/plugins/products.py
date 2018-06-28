# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import Category, ProductCrossSell, ProductCrossSellType
from shuup.front.template_helpers.general import (
    get_best_selling_products, get_newest_products,
    get_products_for_categories, get_random_products
)
from shuup.front.template_helpers.product import map_relation_type
from shuup.xtheme import TemplatedPlugin
from shuup.xtheme.plugins.forms import GenericPluginForm, TranslatableField
from shuup.xtheme.plugins.widgets import XThemeModelChoiceField


class ProductHighlightPlugin(TemplatedPlugin):
    identifier = "product_highlight"
    name = _("Product Highlights")
    template_name = "shuup/xtheme/plugins/highlight_plugin.jinja"
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("type", forms.ChoiceField(label=_("Type"), choices=[
            ("newest", "Newest"),
            ("best_selling", "Best Selling"),
            ("random", "Random"),
        ], initial="newest")),
        ("count", forms.IntegerField(label=_("Count"), min_value=1, initial=4)),
        ("orderable_only", forms.BooleanField(label=_("Only show in-stock and orderable items"),
                                              initial=True,
                                              required=False))
    ]

    def get_context_data(self, context):
        type = self.config.get("type", "newest")
        count = self.config.get("count", 4)
        orderable_only = self.config.get("orderable_only", True)
        if type == "newest":
            products = get_newest_products(context, count, orderable_only)
        elif type == "best_selling":
            products = get_best_selling_products(context, count, orderable_only=orderable_only)
        elif type == "random":
            products = get_random_products(context, count, orderable_only)
        else:
            products = []

        return {
            "request": context["request"],
            "title": self.get_translated_value("title"),
            "products": products
        }


class ProductCrossSellsPlugin(TemplatedPlugin):
    identifier = "product_cross_sells"
    name = _("Product Cross Sells")
    template_name = "shuup/xtheme/plugins/cross_sells_plugin.jinja"
    required_context_variables = ["product"]
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("type", ProductCrossSell.type.field.formfield()),
        ("count", forms.IntegerField(label=_("Count"), min_value=1, initial=4)),
        ("orderable_only", forms.BooleanField(label=_("Only show in-stock and orderable items"),
                                              initial=True,
                                              required=False))
    ]

    def __init__(self, config):
        relation_type = config.get("type", None)
        if relation_type:
            # Map initial config string to enum type
            try:
                type = map_relation_type(relation_type)
            except LookupError:
                type = ProductCrossSellType.RELATED
            config["type"] = type
        super(ProductCrossSellsPlugin, self).__init__(config)

    def get_context_data(self, context):
        count = self.config.get("count", 4)
        product = context.get("product", None)
        orderable_only = self.config.get("orderable_only", True)
        relation_type = self.config.get("type")
        try:
            type = map_relation_type(relation_type)
        except LookupError:
            type = ProductCrossSellType.RELATED
        return {
            "request": context["request"],
            "title": self.get_translated_value("title"),
            "product": product,
            "type": type,
            "count": count,
            "orderable_only": orderable_only,
        }


class ProductsFromCategoryForm(GenericPluginForm):
    def populate(self):
        for field in self.plugin.fields:
            if isinstance(field, tuple):
                name, value = field
                value.initial = self.plugin.config.get(name, value.initial)
                self.fields[name] = value
        self.fields["category"] = XThemeModelChoiceField(
            label=_("category"),
            queryset=Category.objects.all(),
            required=False,
            initial=self.plugin.config.get("category") if self.plugin else None
        )

    def clean(self):
        cleaned_data = super(ProductsFromCategoryForm, self).clean()
        carousel = cleaned_data.get("category")
        cleaned_data["category"] = carousel.pk if hasattr(carousel, "pk") else None
        return cleaned_data


class ProductsFromCategoryPlugin(TemplatedPlugin):
    identifier = "category_products"
    name = _("Category Products Highlight")
    template_name = "shuup/xtheme/plugins/highlight_plugin.jinja"
    editor_form_class = ProductsFromCategoryForm
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("count", forms.IntegerField(label=_("Count"), min_value=1, initial=4)),
        "category",
    ]

    def get_context_data(self, context):
        products = []
        category_id = self.config.get("category")
        count = self.config.get("count")
        category = Category.objects.filter(id=category_id).first() if category_id else None
        if category:
            products = get_products_for_categories(context, [category], n_products=count)
        return {
            "request": context["request"],
            "title": self.get_translated_value("title"),
            "products": products
        }
