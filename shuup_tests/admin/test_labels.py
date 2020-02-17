# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from django.core.urlresolvers import reverse
from django.utils.translation import activate

from shuup.admin.modules.labels.views import LabelEditView, LabelDeleteView
from shuup.core.models import Label
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_labels_edit_and_delete(rf, admin_user):
    activate("en")
    label = Label.objects.create(identifier="test-label", name="Test")

    assert Label.objects.count() == 1
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    edit_view = LabelEditView.as_view()
    response = edit_view(request, pk=label.pk)
    assert response.status_code == 200

    request = apply_request_middleware(rf.post("/"), user=admin_user)
    delete_view = LabelDeleteView.as_view()
    response = delete_view(request, pk=label.pk)
    assert response.status_code == 302  # Redirect to list view
    assert Label.objects.count() == 0
