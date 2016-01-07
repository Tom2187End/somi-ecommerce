# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField


class PersistentCacheEntry(models.Model):
    module = models.CharField(max_length=64)
    key = models.CharField(max_length=64)
    time = models.DateTimeField(auto_now=True)
    data = JSONField()

    class Meta:
        verbose_name = _('cache entry')
        verbose_name_plural = _('cache entries')
        unique_together = (('module', 'key'),)
