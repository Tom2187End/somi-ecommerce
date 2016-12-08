# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import zipfile

from django.http import HttpResponse, JsonResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from six import BytesIO

from shuup.admin.utils.picotable import (
    PicotableFileMassAction, PicotableMassAction
)
from shuup.core.models import Order, Shipment
from shuup.order_printouts.admin_module.views import (
    get_confirmation_pdf, get_delivery_pdf
)


class CancelOrderAction(PicotableMassAction):
    label = _("Cancel")
    identifier = "mass_action_order_cancel"

    def process(self, request, ids):
        for order in Order.objects.filter(pk__in=ids):
            if not order.can_set_canceled():
                continue
            order.set_canceled()


class OrderConfirmationPdfAction(PicotableFileMassAction):
    label = _("Print Confirmation PDF(s)")
    identifier = "mass_action_order_confirmation_pdf"

    def process(self, request, ids):
        if len(ids) == 1:
            try:
                response = get_confirmation_pdf(request, ids[0])
                response['Content-Disposition'] = 'attachment; filename=order_%s_confirmation.pdf' % ids[0]
                return response
            except Exception as e:
                msg = e.message if hasattr(e, "message") else e
                return JsonResponse({"error": force_text(msg)})

        buff = BytesIO()
        archive = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)
        added = 0
        errors = []
        for id in ids:
            try:
                pdf_file = get_confirmation_pdf(request, id)
                filename = "order_%d_confirmation.pdf" % id
                archive.writestr(filename, pdf_file.content)
                added += 1
            except Exception as e:
                msg = e.message if hasattr(e, "message") else e
                errors.append(force_text(msg))
                continue
        if added:
            archive.close()
            buff.flush()
            ret_zip = buff.getvalue()
            buff.close()
            response = HttpResponse(content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=order_confirmation_pdf.zip'
            response.write(ret_zip)
            return response
        return JsonResponse({"errors": errors})


class OrderDeliveryPdfAction(PicotableFileMassAction):
    label = _("Print Delivery PDF(s)")
    identifier = "mass_action_order_delivery_pdf"

    def process(self, request, ids):
        shipment_ids = set(Shipment.objects.filter(order_id__in=ids).values_list("id", flat=True))
        if len(shipment_ids) == 1:
            try:
                response = get_delivery_pdf(request, ids[0])
                response['Content-Disposition'] = 'attachment; filename=shipment_%s_delivery.pdf' % ids[0]
                return response
            except Exception as e:
                msg = e.message if hasattr(e, "message") else e
                return JsonResponse({"error": force_text(msg)})
        buff = BytesIO()
        archive = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)

        added = 0
        errors = []
        for id in shipment_ids:
            try:
                pdf_file = get_delivery_pdf(request, id)
                filename = "shipment_%d_delivery.pdf" % id
                archive.writestr(filename, pdf_file.content)
                added += 1
            except Exception as e:
                msg = e.message if hasattr(e, "message") else e
                errors.append(force_text(msg))
                continue
        if added:
            archive.close()
            buff.flush()
            ret_zip = buff.getvalue()
            buff.close()
            response = HttpResponse(content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=order_delivery_pdf.zip'
            response.write(ret_zip)
            return response
        return JsonResponse({"errors": errors})
