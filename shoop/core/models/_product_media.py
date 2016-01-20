# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from easy_thumbnails.files import get_thumbnailer
from enumfields import Enum, EnumIntegerField
from filer.fields.file import FilerFileField
from parler.models import TranslatableModel, TranslatedFields

from shoop.core.fields import InternalIdentifierField


class ProductMediaKind(Enum):
    GENERIC_FILE = 1
    IMAGE = 2
    DOCUMENTATION = 3
    SAMPLE = 4

    class Labels:
        GENERIC_FILE = _('file')
        IMAGE = _('image')
        DOCUMENTATION = _('documentation')
        SAMPLE = _('sample')


@python_2_unicode_compatible
class ProductMedia(TranslatableModel):
    identifier = InternalIdentifierField(unique=True)
    product = models.ForeignKey("Product", related_name="media", on_delete=models.CASCADE, verbose_name=_('product'))
    shops = models.ManyToManyField("Shop", related_name="product_media", verbose_name=_('shops'))
    kind = EnumIntegerField(
        ProductMediaKind, db_index=True, default=ProductMediaKind.GENERIC_FILE, verbose_name=_('kind')
    )
    file = FilerFileField(blank=True, null=True, verbose_name=_('file'), on_delete=models.CASCADE)
    external_url = models.URLField(
        blank=True, null=True, verbose_name=_('URL'),
        help_text=_("Enter URL to external file. If this field is filled, the selected media doesn't apply.")
    )
    ordering = models.IntegerField(default=0, verbose_name=_('ordering'))

    # Status
    enabled = models.BooleanField(db_index=True, default=True, verbose_name=_("enabled"))
    public = models.BooleanField(default=True, blank=True, verbose_name=_('public (shown on product page)'))
    purchased = models.BooleanField(
        default=False, blank=True, verbose_name=_('purchased (shown for finished purchases)')
    )

    translations = TranslatedFields(
        title=models.CharField(blank=True, max_length=128, verbose_name=_('title')),
        description=models.TextField(blank=True, verbose_name=_('description')),
    )

    class Meta:
        verbose_name = _('product attachment')
        verbose_name_plural = _('product attachments')
        ordering = ["ordering", ]

    def __str__(self):  # pragma: no cover
        return self.effective_title

    @property
    def effective_title(self):
        title = self.safe_translation_getter("title")
        if title:
            return title

        if self.file_id:
            return self.file.label

        if self.external_url:
            return self.external_url

        return _('attachment')

    @property
    def url(self):
        if self.external_url:
            return self.external_url
        if self.file:
            return self.file.url
        return ""

    @property
    def easy_thumbnails_thumbnailer(self):
        """
        Get `Thumbnailer` instance.

        Will return `None` if file cannot be thumbnailed.

        :rtype:easy_thumbnails.files.Thumbnailer|None
        """
        if not self.file_id:
            return None

        if self.kind != ProductMediaKind.IMAGE:
            return None

        return get_thumbnailer(self.file)

    def get_thumbnail(self, **kwargs):
        """
        Get thumbnail for image

        This will return `None` if there is no file or kind is not `ProductMediaKind.IMAGE`

        :rtype: easy_thumbnails.files.ThumbnailFile|None
        """
        kwargs.setdefault("size", (64, 64))
        kwargs.setdefault("crop", True)  # sane defaults
        kwargs.setdefault("upscale", True)  # sane defaults

        if kwargs["size"] is (0, 0):
            return None

        thumbnailer = self.easy_thumbnails_thumbnailer

        if not thumbnailer:
            return None

        return thumbnailer.get_thumbnail(thumbnail_options=kwargs)
