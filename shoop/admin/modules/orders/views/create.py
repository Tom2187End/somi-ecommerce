# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import traceback

from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from django.http.response import HttpResponse, JsonResponse
from django.test.client import RequestFactory
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from shoop.admin.modules.orders.json_order_creator import JsonOrderCreator
from shoop.admin.utils.urls import get_model_url
from shoop.core.models import Contact, MethodStatus, Order, Product, ShippingMethod, Shop, ShopStatus
from shoop.core.pricing import get_pricing_module


def create_order_from_state(state, **kwargs):
    joc = JsonOrderCreator()
    order = joc.create_order_from_state(state, **kwargs)
    if not order:
        raise ValidationError(list(joc.errors))
    return order


class OrderCreateView(TemplateView):
    model = Order
    template_name = "shoop/admin/orders/create.jinja"
    context_object_name = "order"
    title = _("Create Order")

    def get_context_data(self, **kwargs):
        context = super(OrderCreateView, self).get_context_data(**kwargs)
        context["config"] = self.get_config()
        return context

    def get_config(self):
        def encode_shop(shop):
            return {
                "id": shop.pk,
                "name": force_text(shop),
                "currency": shop.currency,
                "pricesIncludeTax": shop.prices_include_tax
            }

        def encode_method(method):
            return {
                "id": method.pk,
                "name": force_text(method),
            }

        shops = [encode_shop(shop) for shop in Shop.objects.filter(status=ShopStatus.ENABLED)]
        shipping_methods = [encode_method(sm) for sm in ShippingMethod.objects.filter(status=MethodStatus.ENABLED)]

        return {
            "shops": shops,
            "shippingMethods": shipping_methods
        }

    def dispatch(self, request, *args, **kwargs):
        if request.GET.get("command"):
            return self.dispatch_command(request)
        return super(OrderCreateView, self).dispatch(request, *args, **kwargs)

    def dispatch_command(self, request):
        handler = getattr(self, "handle_%s" % request.GET.get("command"), None)
        if not callable(handler):
            return JsonResponse({"error": "unknown command %s" % request.GET.get("command")}, status=400)
        retval = handler(request)
        if not isinstance(retval, HttpResponse):
            retval = JsonResponse(retval)
        return retval

    def handle_product_data(self, request):
        product_id = request.GET["id"]
        shop_id = request.GET["shop_id"]
        customer_id = request.GET.get("customer_id")
        product = Product.objects.get(pk=product_id)
        shop = Shop.objects.get(pk=shop_id)
        ctx_request = RequestFactory().get("/")
        ctx_request.shop = shop
        ctx_request.customer = Contact.objects.filter(pk=customer_id).first()
        ctx_request.user = AnonymousUser()
        context = get_pricing_module().get_context_from_request(ctx_request)
        price_info = product.get_price_info(context, quantity=1)
        return {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "taxClass": {
                "id": product.tax_class.id,
                "name": force_text(product.tax_class),
            },
            "unitPrice": {
                "value": price_info.price.value,  # TODO: This is always zero?!
                "includesTax": price_info.price.includes_tax
            }
        }

    @atomic
    def handle_create(self, request):
        try:
            state = json.loads(request.body.decode("utf-8"))["state"]
            order = create_order_from_state(state, creator=request.user)
            messages.success(request, _("Order %(identifier)s created.") % vars(order))
            return JsonResponse({
                "success": True,
                "orderIdentifier": order.identifier,
                "url": get_model_url(order)
            })
        except Exception as exc:
            tb = traceback.format_exc()
            message = _("Could not create order:")
            if isinstance(exc, ValidationError):  # pragma: no branch
                message += "\n" + "\n".join(force_text(err) for err in exc.messages)
            else:
                message += " " + tb  # pragma: no cover
            return JsonResponse({"success": False, "errorMessage": message}, status=400)
