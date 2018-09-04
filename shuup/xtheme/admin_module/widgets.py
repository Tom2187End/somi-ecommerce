# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.forms import Textarea


class CodeEditorWidget(Textarea):
    def render(self, name, value, attrs=None, renderer=None):
        attrs_for_textarea = attrs.copy()
        attrs_for_textarea["id"] += "-snippet"
        attrs_for_textarea["class"] += " snippet-editor-textarea"
        return super(CodeEditorWidget, self).render(name, value, attrs_for_textarea)
