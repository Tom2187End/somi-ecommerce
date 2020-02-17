# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import absolute_import

import django
import hashlib

import six
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _
from django.forms.models import modelform_factory
from filer.models import File, Folder, Image

from shuup.core.models import MediaFile, MediaFolder


def file_size_validator(value):
    size = getattr(value, "size", None)
    if size and settings.SHUUP_MAX_UPLOAD_SIZE and settings.SHUUP_MAX_UPLOAD_SIZE < size:
        raise ValidationError(
            _("Maximum file size reached (%(size)s MB)") % {"size": settings.SHUUP_MAX_UPLOAD_SIZE / 1000 / 1000},
            code="file_max_size_reached"
        )

    return value


if django.VERSION < (1, 11):
    class UploadFileForm(forms.Form):
        file = forms.FileField(validators=[file_size_validator])
else:
    from django.core.validators import FileExtensionValidator

    class UploadFileForm(forms.Form):
        file = forms.FileField(validators=[
            FileExtensionValidator(allowed_extensions=settings.SHUUP_ALLOWED_UPLOAD_EXTENSIONS),
            file_size_validator
        ])


class UploadImageForm(forms.Form):
    file = forms.ImageField(validators=[file_size_validator])


def filer_folder_from_path(path):
    """
    Split `path` by slashes and create a hierarchy of Filer Folder objects accordingly.
    Blank path components are ignored, so "/////foo//////bar///" is the same as "foo/bar".

    The empty string (and `None`) are handled as "no folder", i.e. root folder.

    :param path: Pathname or None
    :type path: str|None
    :return: Folder
    :rtype: filer.models.Folder
    """
    if path is None:
        return None
    folder = None
    for component in six.text_type(path).split("/"):
        if component:
            folder = Folder.objects.get_or_create(name=component, parent=folder)[0]
    return folder


def _filer_file_from_upload(model, request, path, upload_data, sha1=None):
    """
    Create some sort of Filer file (either File or Image, really) from the given upload data (ContentFile or UploadFile)

    :param model: Model class
    :param request: Request, to figure out the owner for this file
    :type request: django.http.request.HttpRequest|None
    :param path: Pathname string (see `filer_folder_from_path`) or a Filer Folder.
    :type path: basestring|filer.models.Folder
    :param upload_data: Upload data
    :type upload_data: django.core.files.base.File
    :param sha1: SHA1 checksum. If given and a matching `model` with the SHA1 is found, it is returned instead.
    :type sha1: basestring

    :return: Filer file
    """
    if sha1:
        upload = model.objects.filter(sha1=sha1).first()
        if upload:
            return upload

    file_form_cls = modelform_factory(
        model=model, fields=('original_filename', 'owner', 'file'))
    upload_form = file_form_cls(
        data={
            'original_filename': upload_data.name,
            'owner': (request.user.pk if (request and not request.user.is_anonymous()) else None)
        },
        files={
            'file': upload_data
        }
    )
    upload = upload_form.save(commit=False)
    upload.is_public = True
    if isinstance(path, Folder):
        upload.folder = path
    else:
        upload.folder = filer_folder_from_path(path)
    upload.save()
    return upload


def filer_file_from_upload(request, path, upload_data, sha1=None):
    """
    Create a filer.models.filemodels.File from an upload (UploadedFile or such).
    If the `sha1` parameter is passed and a file with said SHA1 is found, it will be returned instead.

    :param request: Request, to figure out the owner for this file
    :type request: django.http.request.HttpRequest|None
    :param path: Pathname string (see `filer_folder_from_path`) or a Filer Folder.
    :type path: basestring|filer.models.Folder
    :param upload_data: Upload data
    :type upload_data: django.core.files.base.File
    :param sha1: SHA1 checksum. If given and a matching `model` with the SHA1 is found, it is returned instead.
    :type sha1: basestring

    :rtype: filer.models.filemodels.File
    """
    return _filer_file_from_upload(model=File, request=request, path=path, upload_data=upload_data, sha1=sha1)


def filer_image_from_upload(request, path, upload_data, sha1=None):
    """
    Create a Filer Image from an upload (UploadedFile or such).
    If the `sha1` parameter is passed and an Image with said SHA1 is found, it will be returned instead.

    :param request: Request, to figure out the owner for this file
    :type request: django.http.request.HttpRequest|None
    :param path: Pathname string (see `filer_folder_from_path`) or a Filer Folder.
    :type path: basestring|filer.models.Folder
    :param upload_data: Upload data
    :type upload_data: django.core.files.base.File
    :param sha1: SHA-1 checksum of the data, if available, to do deduplication
    :type sha1: basestring

    :rtype: filer.models.imagemodels.Image
    """
    return _filer_file_from_upload(model=Image, request=request, path=path, upload_data=upload_data, sha1=sha1)


def filer_image_from_data(request, path, file_name, file_data, sha1=None):
    """
    Create a Filer Image from the given data string.
    If the `sha1` parameter is passed and True (the value True, not a truey value), the SHA-1 of the data string
    is calculated and passed to the underlying creation function.
    If the `sha1` parameter is truthy (generally the SHA-1 hex string), it's passed directly to the creation function.

    :param request: Request, to figure out the owner for this file
    :type request: django.http.request.HttpRequest|None
    :param path: Pathname string (see `filer_folder_from_path`) or a Filer Folder.
    :type path: basestring|filer.models.Folder
    :param file_name: File name
    :type file_data: basestring
    :param file_data: Upload data
    :type file_data: bytes
    :param sha1: SHA-1 checksum of the data, if available, to do deduplication.
                 May also be `True` to calculate the SHA-1 first.
    :type sha1: basestring|bool

    :rtype: filer.models.imagemodels.Image
    """
    if sha1 is True:
        sha1 = hashlib.sha1(file_data).hexdigest()
    upload_data = ContentFile(file_data, file_name)
    return _filer_file_from_upload(model=Image, request=request, path=path, upload_data=upload_data, sha1=sha1)


def filer_file_to_json_dict(file):
    """
    :type file: filer.models.File
    :rtype: dict
    """
    assert file.is_public

    try:
        thumbnail = file.easy_thumbnails_thumbnailer.get_thumbnail({
            'size': (128, 128),
            'crop': True,
            'upscale': True,
            'subject_location': file.subject_location
        })
    except Exception:
        thumbnail = None
    return {
        "id": file.id,
        "name": file.label,
        "size": file.size,
        "url": file.url,
        "thumbnail": (thumbnail.url if thumbnail else None),
        "date": file.uploaded_at.isoformat()
    }


def filer_folder_to_json_dict(folder, children=None):
    """
    :type file: filer.models.Folder|None
    :type children: list(filer.models.Folder)
    :rtype: dict
    """
    if folder and children is None:
        # This allows us to pass `None` as a pseudo root folder
        children = folder.get_children()
    return {
        "id": folder.pk if folder else 0,
        "name": folder.name if folder else _("Root"),
        "children": [filer_folder_to_json_dict(child) for child in children]
    }


def ensure_media_folder(shop, folder):
    media_folder, created = MediaFolder.objects.get_or_create(folder=folder)
    if not media_folder.shops.filter(id=shop.id).exists():
        media_folder.shops.add(shop)


def ensure_media_file(shop, file):
    media_file, created = MediaFile.objects.get_or_create(file=file)
    if not media_file.shops.filter(id=shop.id).exists():
        media_file.shops.add(shop)
