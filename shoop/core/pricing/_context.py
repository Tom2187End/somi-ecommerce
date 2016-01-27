# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import abc

import six
from django.http import HttpRequest
from django.utils.timezone import now


class PricingContextable(six.with_metaclass(abc.ABCMeta)):
    """
    Object that is or can be converted to a pricing context.

    Currently there exists two kind of `PricingContextable` objects:
    `PricingContext`(and its subclasses) and `HttpRequest`.

    .. note::

       Expression ``isinstance(request, PricingContextable)`` will
       return True for a ``request`` which is `HttpRequest`, because
       `HttpRequest` is registered as a subclass of this abstract base
       class.

    This abstract base class is just a helper to allow writing simpler
    type specifiers, since we want to allow passing `HttpRequest` as a
    pricing context even though it is not a `PricingContext`.
    """
    pass
PricingContextable.register(HttpRequest)


class PricingContext(PricingContextable):
    """
    Context for pricing.
    """
    def __init__(self, shop, customer, time=None):
        """
        Initialize pricing context for shop and customer.

        :type shop: shoop.core.models.Shop
        :type customer: shoop.core.models.Contact
        :type time: datetime.datetime|None
        """
        self.shop = shop
        self.customer = customer
        self.time = (time if time is not None else now())
