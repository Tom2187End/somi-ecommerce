# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import View
from six.moves import urllib

from shuup.front.checkout import CheckoutProcess
from shuup.utils.importing import cached_load

__all__ = ["BaseCheckoutView"]


class BaseCheckoutView(View):
    phase_specs = []
    empty_phase_spec = None

    def dispatch(self, request, *args, **kwargs):
        if request.basket.is_empty and self.empty_phase_spec:
            self.phase_specs = [self.empty_phase_spec]

        process = CheckoutProcess(
            phase_specs=self.phase_specs,
            phase_kwargs=dict(request=self.request, args=self.args, kwargs=self.kwargs)
        )
        phase_identifier = kwargs.get("phase")
        if phase_identifier == "reset":
            process.reset()
            return redirect("shuup:checkout")

        current_phase = process.prepare_current_phase(phase_identifier)
        if not current_phase.final and current_phase.identifier != phase_identifier:
            url = reverse("shuup:checkout", kwargs={"phase": current_phase.identifier})
            params = ("?" + urllib.parse.urlencode(request.GET)) if request.GET else ""
            return redirect(url + params)
        return current_phase.dispatch(request, *args, **kwargs)


class DefaultCheckoutView(BaseCheckoutView):
    phase_specs = [
        "shuup.front.checkout.addresses:AddressesPhase",
        "shuup.front.checkout.methods:MethodsPhase",
        "shuup.front.checkout.methods:ShippingMethodPhase",
        "shuup.front.checkout.methods:PaymentMethodPhase",
        "shuup.front.checkout.confirm:ConfirmPhase",
    ]
    empty_phase_spec = "shuup.front.checkout.empty:EmptyPhase"


class SinglePhaseCheckoutView(BaseCheckoutView):
    phase_specs = [
        "shuup.front.checkout.single_page.SingleCheckoutPhase"
    ]
    empty_phase_spec = None  # Use the same phase specs when the basket is empty


def get_checkout_view():
    view = cached_load("SHUUP_CHECKOUT_VIEW_SPEC")
    if hasattr(view, "as_view"):  # pragma: no branch
        view = view.as_view()
    return view
