# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from shoop.core.fields import InternalIdentifierField


__all__ = ("Manufacturer",)


@python_2_unicode_compatible
class Manufacturer(models.Model):
    created_on = models.DateTimeField(auto_now_add=True, verbose_name=_('added'))
    identifier = InternalIdentifierField()

    name = models.CharField(max_length=128, verbose_name=_('name'))
    url = models.CharField(null=True, blank=True, max_length=128, verbose_name=_('URL'))

    class Meta:
        verbose_name = _('manufacturer')
        verbose_name_plural = _('manufacturers')

    def __str__(self):  # pragma: no cover
        return u'%s' % (self.name)
