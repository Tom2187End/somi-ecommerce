# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.utils.form_group import FormGroup
from shuup.xtheme.layout import LayoutCell


class LayoutCellGeneralInfoForm(forms.Form):
    plugin = forms.ChoiceField(label=_("Plugin"), required=False)

    CELL_FULL_WIDTH = 12

    CELL_WIDTH_CHOICES = [
        (int(CELL_FULL_WIDTH), _("Full Width")),
        (int(CELL_FULL_WIDTH * 3 / 4), _("Three Fourths (3/4)")),
        (int(CELL_FULL_WIDTH * 2 / 3), _("Two Thirds (2/3)")),
        (int(CELL_FULL_WIDTH / 2), _("Half (1/2)")),
        (int(CELL_FULL_WIDTH / 3), _("One Third (1/3)")),
        (int(CELL_FULL_WIDTH / 4), _("One Fourth (1/4)")),
    ]

    def __init__(self, **kwargs):
        self.layout_cell = kwargs.pop("layout_cell")
        self.theme = kwargs.pop("theme")
        super(LayoutCellGeneralInfoForm, self).__init__(**kwargs)
        self.populate()

    def populate(self):
        """
        Populate the form with fields for size and plugin selection.
        """

        initial_cell_width = self.layout_cell.sizes.get("sm") or self.CELL_FULL_WIDTH

        self.fields["cell_width"] = forms.ChoiceField(
            label=_("Cell width"), choices=self.CELL_WIDTH_CHOICES, initial=initial_cell_width)

        if self.theme:
            plugin_choices = self.theme.get_all_plugin_choices(empty_label=_("No Plugin"))
            plugin_field = self.fields["plugin"]
            plugin_field.choices = plugin_field.widget.choices = plugin_choices
            plugin_field.initial = self.layout_cell.plugin_identifier

    def save(self):
        """
        Save size configuration. Plugin configuration is done via JavaScript POST.

        Both breakpoints (`sm`and `md`) are set to same value defined in `cell_width_field`.
        The reason for this is that the difference between these breakpoints is so
        minor that manually assigning both of these by shop admin introduces too much
        complexity to row-cell management UI.
        """
        data = self.cleaned_data
        sizes = ["sm", "md"]  # TODO: Parametrize? Currently Bootstrap dependent.
        for size in sizes:
            self.layout_cell.sizes[size] = int(data["cell_width"])


class LayoutCellFormGroup(FormGroup):
    """
    Form group containing the LayoutCellGeneralInfoForm and a possible plugin-dependent configuration form.
    """
    def __init__(self, **kwargs):
        self.layout_cell = kwargs.pop("layout_cell")
        self.theme = kwargs.pop("theme")
        assert isinstance(self.layout_cell, LayoutCell)
        super(LayoutCellFormGroup, self).__init__(**kwargs)
        self.add_form_def("general", LayoutCellGeneralInfoForm, kwargs={
            "layout_cell": self.layout_cell,
            "theme": self.theme
        })
        plugin = self.layout_cell.instantiate_plugin(theme=self.theme)
        if plugin:
            form_class = plugin.get_editor_form_class()
            if form_class:
                self.add_form_def("plugin", form_class, kwargs={"plugin": plugin})

    def save(self):
        self.forms["general"].save()
        plugin_form = self.forms.get("plugin")
        if plugin_form:
            self.layout_cell.config = plugin_form.get_config()
