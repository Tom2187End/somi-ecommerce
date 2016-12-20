# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.response import Response


class ProtectedModelViewSetMixin(object):

    def destroy(self, request, *args, **kwargs):
        try:
            return super(ProtectedModelViewSetMixin, self).destroy(request, *args, **kwargs)
        except ProtectedError as exc:
            ref_obj = exc.protected_objects[0].__class__.__name__
            msg = "This object can not be deleted because it is referenced by {}".format(ref_obj)
            return Response(data={"error": msg}, status=status.HTTP_400_BAD_REQUEST)
