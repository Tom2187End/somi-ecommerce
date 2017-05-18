# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import exceptions, serializers, status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from shuup.api.decorators import schema_serializer_class
from shuup.api.fields import EnumField
from shuup.api.mixins import PermissionHelperMixin
from shuup.core.api.address import AddressSerializer
from shuup.core.api.contacts import PersonContactSerializer
from shuup.core.basket import (
    get_basket_command_dispatcher, get_basket_order_creator
)
from shuup.core.basket.storage import BasketCompatibilityError
from shuup.core.excs import ProductNotOrderableProblem
from shuup.core.fields import (
    FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES, FORMATTED_DECIMAL_FIELD_MAX_DIGITS
)
from shuup.core.models import (
    Basket, Contact, get_company_contact, get_person_contact, MutableAddress,
    Order, OrderLineType, OrderStatus, PaymentMethod, Product, ShippingMethod,
    Shop, ShopProduct
)
from shuup.utils.importing import cached_load

from .service import PaymentMethodSerializer, ShippingMethodSerializer


def get_shop_id(uuid):
    try:
        return int(uuid.split("-")[0])
    except ValueError:
        raise exceptions.ValidationError("Malformed UUID")


def get_key(uuid):
    try:
        return uuid.split("-")[1]
    except (ValueError, IndexError):
        raise exceptions.ValidationError("Malformed UUID")


class BasketProductSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Product)

    class Meta:
        model = Product
        fields = ["id", "translations"]


class BasketCustomerSerializer(PersonContactSerializer):
    default_shipping_address = serializers.PrimaryKeyRelatedField(read_only=True)
    default_billing_address = serializers.PrimaryKeyRelatedField(read_only=True)
    user = serializers.SerializerMethodField()

    class Meta(PersonContactSerializer.Meta):
        exclude = None
        fields = [
            "id",
            "user",
            "name",
            "email",
            "first_name",
            "last_name",
            "phone",
            "default_shipping_method",
            "default_payment_method",
            "default_shipping_address",
            "default_billing_address"
        ]

    def get_user(self, customer):
        user = getattr(customer, 'user', None)
        if user:
            return getattr(user, 'pk', None)


class BasketLineSerializer(serializers.Serializer):
    product = BasketProductSerializer(required=False)
    image = serializers.SerializerMethodField()
    text = serializers.CharField()
    sku = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                        decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                     decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    base_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                          decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    discount_amount = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                               decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    type = EnumField(OrderLineType)
    shop = serializers.SerializerMethodField()
    shop_product = serializers.SerializerMethodField()
    line_id = serializers.CharField()

    def get_image(self, line):
        """ Return simply the primary image URL """

        if not line.product:
            return

        primary_image = line.product.primary_image

        # no image found
        if not primary_image:
            # check for variation parent image
            if not line.product.variation_parent or not line.product.variation_parent.primary_image:
                return

            primary_image = line.product.variation_parent.primary_image

        if primary_image.external_url:
            return primary_image.external_url
        else:
            return self.context["request"].build_absolute_uri(primary_image.file.url)

    def get_shop_product(self, line):
        return line.shop_product.id if line.product else None

    def get_shop(self, line):
        return line.shop.id if line.shop else None


class BasketSerializer(serializers.Serializer):
    shop = serializers.SerializerMethodField()
    key = serializers.CharField(max_length=32, min_length=32)
    items = serializers.SerializerMethodField()
    unorderable_items = serializers.SerializerMethodField()
    codes = serializers.ListField()
    shipping_address = serializers.SerializerMethodField()
    shipping_method = ShippingMethodSerializer()
    payment_method = PaymentMethodSerializer()
    customer = BasketCustomerSerializer()
    total_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                           decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    total_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                           decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxful_total_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                  decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxless_total_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                   decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    total_discount = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                              decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxful_total_discount = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                     decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxless_total_discount = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                      decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    total_price_of_products = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                       decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    validation_errors = serializers.SerializerMethodField()

    def get_shipping_address(self, basket):
        if basket._data.get('shipping_address_id'):
            address = MutableAddress.objects.filter(id=basket._data['shipping_address_id']).first()
            return AddressSerializer(address, context=self.context).data

    def get_validation_errors(self, basket):
        return [{err.code: "%s" % err.message} for err in basket.get_validation_errors()]

    def get_items(self, basket):
        return BasketLineSerializer(basket.get_final_lines(with_taxes=True), many=True, context=self.context).data

    def get_unorderable_items(self, basket):
        return BasketLineSerializer(basket.get_unorderable_lines(), many=True, context=self.context).data

    def get_shop(self, basket):
        return basket.shop.id


class StoredBasketSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Basket


class BaseProductAddBasketSerializer(serializers.Serializer):
    supplier = serializers.IntegerField(required=False)
    quantity = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                        decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES,
                                        required=False)


class ShopProductAddBasketSerializer(BaseProductAddBasketSerializer):
    shop_product = serializers.PrimaryKeyRelatedField(queryset=ShopProduct.objects.all())
    shop = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()

    def get_shop(self, line):
        return line.get("shop_product").shop.pk

    def get_product(self, line):
        return line.get("shop_product").product.pk

    def validate(self, data):
        # TODO - we probably eventually want this ability
        if self.context["shop"].pk != data.get("shop_product").shop.pk:
            raise serializers.ValidationError(
                "It is not possible to add a product from a different shop in the basket.")
        return data


class ProductAddBasketSerializer(BaseProductAddBasketSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    def validate(self, data):
        # TODO - we probably eventually want this ability
        if self.context["shop"].pk != data.get("shop").pk:
            raise serializers.ValidationError(
                "It is not possible to add a product from a different shop in the basket.")
        return data


class RemoveBasketSerializer(serializers.Serializer):
    line_id = serializers.CharField()


class LineQuantitySerializer(serializers.Serializer):
    line_id = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                        decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)


class MethodIDSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)


class CodeAddBasketSerializer(serializers.Serializer):
    code = serializers.CharField()


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "reference_number"]


class BasketViewSet(PermissionHelperMixin, viewsets.ViewSet):
    """
    This class contains all methods to manage the request basket.

    The endpoints just forward commands to the configured `BasketCommandDispatcher`
    assuming it has the following ones:

    - `add` - to add a shop product
    - `update` - to update/remove an order line
        (the expected kwargs should be q_ to update and remove_ to delete a line)
    - `clean` - remove all lines and codes from the basket
    - `add_campaign_code` - add a coupon code to the basket

    """

    # just to make use of the convenient ViewSet class
    queryset = Product.objects.none()
    lookup_field = "uuid"

    def get_view_name(self):
        return _("Basket")

    @classmethod
    def get_help_text(cls):
        return _("Basket items can be listed, added, removed and cleaned. Also campaign codes can be added.")

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'source': getattr(self.request, "basket", None),
            'format': self.format_kwarg,
            'view': self
        }

    def get_basket_shop(self):
        if settings.SHUUP_ENABLE_MULTIPLE_SHOPS:
            uuid = self.kwargs.get(self.lookup_field, "")
            if uuid:
                shop_id = get_shop_id(self.kwargs.get(self.lookup_field, ""))
            else:
                # shop will be part of POST'ed data for basket creation
                shop_id = self.request.data.get("shop")
            if not shop_id:
                try:
                    shop_id = self.request.GET["shop"]
                except:
                    raise exceptions.ValidationError("No basket shop specified.")
            # this shop should be the shop associated with the basket
            return get_object_or_404(Shop, pk=shop_id)
        else:
            return Shop.objects.first()

    def process_request(self, with_basket=True):
        """
        Add context to request that's expected by basket
        """
        request = self.request._request
        user = self.request.user
        request.shop = self.get_basket_shop()
        request.person = get_person_contact(user)
        company = get_company_contact(user)
        request.customer = (company or request.person)
        if with_basket:
            request.basket = self.get_object()

    @schema_serializer_class(BasketSerializer)
    def retrieve(self, request, *args, **kwargs):
        """
        List the contents of the basket
        """
        self.process_request()
        return Response(BasketSerializer(request.basket, context=self.get_serializer_context()).data)

    def _get_controlled_contacts_by_user(self, user):
        """
        List of contact ids the user controls

        The list includes the person contact linked to the user and all
        company contacts the user contact is linked to

        :param user: user object
        :type user: settings.USER_MODEL
        :return: list of contact ids the user controls
        :rtype: list(int)
        """
        contact = get_person_contact(user)
        if not contact:
            return []
        return [contact.pk] + list(contact.company_memberships.all().values_list("pk", flat=True))

    def get_object(self):
        uuid = get_key(self.kwargs.get(self.lookup_field, ""))
        shop = self.request.shop
        loaded_basket = Basket.objects.filter(key=uuid).first()

        # ensure correct owner
        if not self.request.user.is_superuser:
            if not loaded_basket.shop == shop:
                raise exceptions.PermissionDenied("No permission")

            customer_id = (loaded_basket.customer.pk if loaded_basket.customer else None)
            controlled_contact_ids = self._get_controlled_contacts_by_user(self.request.user)
            is_staff = self.is_staff_user(shop, self.request.user)
            if customer_id and customer_id not in controlled_contact_ids and not is_staff:
                raise exceptions.PermissionDenied("No permission")

        # actually load basket
        basket_class = cached_load("SHUUP_BASKET_CLASS_SPEC")
        basket = basket_class(self.request._request, basket_name=uuid)

        try:
            basket._data = basket.storage.load(basket)
        except BasketCompatibilityError as error:
            raise exceptions.ValidationError(str(error))

        # Hack: the storage should do this already
        # set the correct basket customer
        if loaded_basket and loaded_basket.customer:
            basket.customer = loaded_basket.customer

        return basket

    def is_staff_user(self, shop, user):
        return (shop and user.is_staff and shop.staff_members.filter(pk=user.pk).exists())

    @list_route(methods=['post'])
    def new(self, request, *args, **kwargs):
        """
        Create a brand new basket object
        """
        self.process_request(with_basket=False)
        basket_class = cached_load("SHUUP_BASKET_CLASS_SPEC")
        basket = basket_class(request._request)

        customer_id = request.POST.get("customer_id")
        if not customer_id:
            customer_id = request.data.get("customer_id")

        if customer_id:
            is_staff = self.is_staff_user(self.request.shop, self.request.user)
            is_superuser = self.request.user.is_superuser

            if int(customer_id) in self._get_controlled_contacts_by_user(self.request.user) or is_superuser or is_staff:
                basket.customer = Contact.objects.get(pk=int(customer_id))
            else:
                raise exceptions.PermissionDenied("No permission")

        stored_basket = basket.save()
        response_data = {
            "uuid": "%s-%s" % (request.shop.pk, stored_basket.key)
        }
        response_data.update(BasketSerializer(basket, context=self.get_serializer_context()).data)
        return Response(data=response_data, status=status.HTTP_201_CREATED)

    def _handle_cmd(self, request, command, kwargs):
        cmd_dispatcher = get_basket_command_dispatcher(request)
        cmd_handler = cmd_dispatcher.get_command_handler(command)
        cmd_kwargs = cmd_dispatcher.preprocess_kwargs(command, kwargs)
        response = cmd_handler(**cmd_kwargs)
        return cmd_dispatcher.postprocess_response(command, cmd_kwargs, response)

    @list_route(methods=['get'])
    def abandoned(self, request, *args, **kwargs):
        self.process_request(with_basket=False)
        days = int(request.GET.get("days_ago", 14))

        days_ago = None
        if days:
            days_ago = now() - datetime.timedelta(days=days)

        not_updated_in_hours = int(request.GET.get("not_updated_in_hours", 2))
        late_cutoff = now() - datetime.timedelta(hours=not_updated_in_hours)

        if days_ago:
            updated_on_q = Q(updated_on__range=(days_ago, late_cutoff))
        else:
            updated_on_q = Q(updated_on__lte=late_cutoff)

        stored_baskets = Basket.objects.filter(
            shop=request.shop
        ).filter(updated_on_q, product_count__gte=0).exclude(
            deleted=True, finished=True, persistent=True
        )
        return Response(StoredBasketSerializer(stored_baskets, many=True).data)

    @schema_serializer_class(ProductAddBasketSerializer)
    @detail_route(methods=['post'])
    def add(self, request, *args, **kwargs):
        """
        Adds a product to the basket
        """
        self.process_request()
        return self._add_product(request, *args, **kwargs)

    @schema_serializer_class(RemoveBasketSerializer)
    @detail_route(methods=['post'])
    def remove(self, request, *args, **kwargs):
        """
        Removes a basket line
        """
        self.process_request()
        serializer = RemoveBasketSerializer(data=request.data)

        if serializer.is_valid():
            cmd_kwargs = {
                "request": request._request,
                "basket": request.basket,
                "delete_{}".format(serializer.validated_data["line_id"]): 1
            }
            try:
                self._handle_cmd(request, "update", cmd_kwargs)
                request.basket.save()
            except ValidationError as exc:
                return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
            else:
                data = BasketSerializer(request.basket, context=self.get_serializer_context()).data
                return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def clear(self, request, *args, **kwargs):
        """
        Clear basket contents
        """
        self.process_request()
        cmd_kwargs = {
            "request": request._request,
            "basket": request.basket
        }
        try:
            self._handle_cmd(request, "clear", cmd_kwargs)
            request.basket.save()
        except ValidationError as exc:
            return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = BasketSerializer(request.basket, context=self.get_serializer_context()).data
            return Response(data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def update_quantity(self, request, *args, **kwargs):
        self.process_request()
        serializer = LineQuantitySerializer(data=request.data)
        if serializer.is_valid():
            cmd_kwargs = {
                "request": request._request,
                "basket": request.basket,
                "q_{}".format(serializer.validated_data["line_id"]): serializer.validated_data["quantity"]
            }
            try:
                self._handle_cmd(request, "update", cmd_kwargs)
                request.basket.save()
            except ValidationError as exc:
                return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
            else:
                data = BasketSerializer(request.basket, context=self.get_serializer_context()).data
                return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @schema_serializer_class(CodeAddBasketSerializer)
    @detail_route(methods=['post'])
    def add_code(self, request, *args, **kwargs):
        """
        Add a campaign code to the basket
        """
        self.process_request()
        serializer = CodeAddBasketSerializer(data=request.data)

        if serializer.is_valid():
            cmd_kwargs = {
                "request": request._request,
                "basket": request.basket,
                "code": serializer.validated_data["code"]
            }
            response = self._handle_cmd(request, "add_campaign_code", cmd_kwargs)
            if response["ok"]:
                data = BasketSerializer(request.basket, context=self.get_serializer_context()).data
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response({"code_invalid": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @schema_serializer_class(AddressSerializer)
    @detail_route(methods=['post'])
    def set_shipping_address(self, request, *args, **kwargs):
        return self._handle_setting_address(request, "shipping_address")

    @schema_serializer_class(AddressSerializer)
    @detail_route(methods=['post'])
    def set_billing_address(self, request, *args, **kwargs):
        return self._handle_setting_address(request, "billing_address")

    def _handle_setting_address(self, request, attr_field):
        """
        Set the address of the basket.
        If ID is sent, the existing MutableAddress will be used instead.
        """
        self.process_request()

        try:
            # take the address by ID
            if request.data.get("id"):
                address = MutableAddress.objects.get(id=request.data['id'])
            else:
                serializer = AddressSerializer(data=request.data)

                if serializer.is_valid():
                    address = serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            setattr(request.basket, attr_field, address)
            request.basket.save()

        except ValidationError as exc:
            return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
        except MutableAddress.DoesNotExist:
            return Response({"error": "Address does not exist"}, status=status.HTTP_404_NOT_FOUND)
        else:
            data = BasketSerializer(request.basket, context=self.get_serializer_context()).data
            return Response(data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def set_shipping_method(self, request, *args, **kwargs):
        return self._handle_setting_method(request, ShippingMethod, "shipping_method")

    @detail_route(methods=['post'])
    def set_payment_method(self, request, *args, **kwargs):
        return self._handle_setting_method(request, PaymentMethod, "payment_method")

    def _handle_setting_method(self, request, model, attr_field):
        self.process_request()
        serializer = MethodIDSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = None
        if request.data.get("id"):
            method = model.objects.get(id=request.data['id'])

        setattr(request.basket, attr_field, method)
        request.basket.save()

        data = BasketSerializer(request.basket, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def create_order(self, request, *args, **kwargs):
        self.process_request()
        request.basket.status = OrderStatus.objects.get_default_initial()
        errors = []
        for error in request.basket.get_validation_errors():
            errors.append({"code": error.code, "message": "%s" % error.message})
        if len(errors):
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        order_creator = get_basket_order_creator()

        customer_id = request.POST.get("customer_id")
        if not customer_id:
            customer_id = request.data.get("customer_id")

        if customer_id:
            # staff and superuser can set custom customer to the basket
            is_staff = self.is_staff_user(self.request.shop, self.request.user)
            is_superuser = self.request.user.is_superuser
            if is_superuser or is_staff:
                from shuup.core.models import PersonContact
                customer = PersonContact.objects.get(pk=customer_id)
                request.basket.customer = customer

        order = order_creator.create_order(request.basket)
        request.basket.finalize()
        return Response(data=OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @detail_route(methods=['post'])
    def add_from_order(self, request, *args, **kwargs):
        """
        Add multiple products to the basket
        """
        self.process_request()
        errors = []
        order_queryset = Order.objects.filter(pk=request.data.get("order"))

        if self.request.basket.customer:
            order_queryset = order_queryset.filter(customer_id=self.request.basket.customer.id)
        else:
            order_queryset = order_queryset.filter(customer_id=get_person_contact(request.user).id)

        order = order_queryset.first()
        if not order:
            return Response({"error": "invalid order"}, status=status.HTTP_404_NOT_FOUND)
        self.clear(request, *args, **kwargs)
        for line in order.lines.products():
            try:
                self._add_product(request, add_data={
                    "product": line.product_id, "shop": order.shop_id, "quantity": line.quantity})
            except ValidationError as exc:
                errors.append({exc.code: exc.message})
            except ProductNotOrderableProblem as exc:
                errors.append({"error": "{}".format(exc)})
            except serializers.ValidationError as exc:
                errors.append({"error": str(exc)})
            except Exception as exc:
                errors.append({"error": str(exc)})
        if len(errors) > 0:
            return Response({"errors": errors}, status.HTTP_400_BAD_REQUEST)
        else:
            return Response(BasketSerializer(request.basket, context=self.get_serializer_context()).data)

    def _add_product(self, request, *args, **kwargs):
        data = kwargs.pop("add_data", request.data)
        if "shop_product" in data:
            serializer = ShopProductAddBasketSerializer(data=data, context={"shop": request.shop})
        else:
            serializer = ProductAddBasketSerializer(data=data, context={"shop": request.shop})

        if serializer.is_valid():
            cmd_kwargs = {
                "request": request._request,
                "basket": request._request.basket,
                "shop_id": serializer.data.get("shop") or serializer.validated_data["shop"].pk,
                "product_id": serializer.data.get("product") or serializer.validated_data["product"].pk,
                "quantity": serializer.validated_data.get("quantity", 1),
                "supplier_id": serializer.validated_data.get("supplier")
            }
            # we call `add` directly, assuming the user will handle variations
            # as he can know all product variations easily through product API
            try:
                self._handle_cmd(request, "add", cmd_kwargs)
                request.basket.save()
            except ValidationError as exc:
                return Response({exc.code: exc.message}, status=status.HTTP_400_BAD_REQUEST)
            except ProductNotOrderableProblem as exc:
                return Response({"error": "{}".format(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as exc:
                return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response(BasketSerializer(request.basket, context=self.get_serializer_context()).data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
