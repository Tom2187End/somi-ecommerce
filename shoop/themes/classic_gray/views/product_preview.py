# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.front.views.product import ProductDetailView


class ProductPreviewView(ProductDetailView):
    template_name = "classic_gray/product_preview.jinja"

    def get_context_data(self, **kwargs):
        # By default the template rendering the basket add form
        # uses the `request.path` as its' `next` value.
        # This is fine if you are on product page but here in
        # preview, we cannot redirect back to `/xtheme/product_preview`.

        context = super(ProductPreviewView, self).get_context_data(**kwargs)
        # Add `return_url` to context to avoid usage of `request.path` in
        # `classic_gray/shoop/front/product/_detail_order_section.jinja`
        context["return_url"] = "/xtheme/products"
        return context


def product_preview(request):
    return ProductPreviewView.as_view()(request, pk=request.GET["id"])
