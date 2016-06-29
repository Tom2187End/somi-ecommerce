# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth.models import Group as PermissionGroup
from django.utils.encoding import force_text

from shoop.admin.base import AdminModule
from shoop.admin.module_registry import get_modules, replace_modules
from shoop.admin.modules.permission_groups.views.edit import (
    PermissionGroupEditView, PermissionGroupForm
)
from shoop.admin.utils.permissions import get_permission_object_from_string
from shoop.testing.factories import get_default_shop
from shoop.testing.utils import apply_request_middleware
from shoop_tests.admin.fixtures.test_module import ARestrictedTestModule
from shoop_tests.utils.fixtures import regular_user


def get_default_permission_group():
    return PermissionGroup.objects.create(name="Test")

@pytest.mark.django_db
def test_permission_group_edit_view(rf, admin_user):
    get_default_shop()
    group = get_default_permission_group()
    view_func = PermissionGroupEditView.as_view()
    response = view_func(apply_request_middleware(rf.get("/", user=admin_user), pk=group.pk))
    assert response.status_code == 200


@pytest.mark.django_db
def test_permission_group_form_updates_members(regular_user):
    with replace_modules([ARestrictedTestModule]):
        modules = [m for m in get_modules()]
        test_module = modules[0]
        module_permissions = test_module.get_required_permissions()

        assert module_permissions

        group = get_default_permission_group()
        form = PermissionGroupForm(instance=group, prefix=None)

        assert not group.permissions.all()
        assert not group.user_set.all()

        data = {
            "name": "New Name",
            "modules": [force_text(test_module.name)],
            "members": [force_text(regular_user.pk)],
        }

        form = PermissionGroupForm(instance=group, prefix=None, data=data)
        form.save()

        module_permissions = [get_permission_object_from_string(m) for m in module_permissions]
        assert group.name == "New Name"
        assert set(module_permissions) == set(group.permissions.all())
        assert regular_user in group.user_set.all()

        form = PermissionGroupForm(instance=group, prefix=None, data={"name": "Name"})
        form.save()

        assert not group.permissions.all()
        assert not group.user_set.all()


def test_only_show_modules_with_defined_names():
    """
    Make sure that only modules with defined names are show as choices
    in admin.
    """
    form = PermissionGroupForm(prefix=None)
    choices = [name for (name, value) in form.fields["modules"].choices]
    assert AdminModule.name not in choices
