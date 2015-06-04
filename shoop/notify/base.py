# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from abc import abstractmethod
from django.utils.text import camel_case_to_spaces
from shoop.notify.enums import UNILINGUAL_TEMPLATE_LANGUAGE
from shoop.utils.text import snake_case
from django.utils.encoding import force_text
from jinja2.exceptions import TemplateError
from shoop.apps.provides import get_identifier_to_object_map
from shoop.notify.enums import ConstantUse, TemplateUse
from shoop.utils.text import space_case
from shoop.notify.template import render_in_context, Template
import six
from .typology import Type


class BaseMetaclass(type):
    def __new__(cls, name, bases, namespace):
        variables = []
        bindings = []
        for key in list(namespace.keys()):
            value = namespace[key]
            if isinstance(value, Binding):
                dest_list = bindings
            elif isinstance(value, Variable):
                dest_list = variables
            else:
                dest_list = None

            if dest_list is not None:
                dest_list.append((key, value))
                del namespace[key]

        namespace.setdefault("variables", {}).update(variables)
        namespace.setdefault("bindings", {}).update(bindings)

        # Figure out some sane defaults
        if "identifier" not in namespace:
            namespace["identifier"] = snake_case(camel_case_to_spaces(name))
        if namespace.get("identifier") and not namespace.get("name"):
            namespace["name"] = space_case(namespace["identifier"]).title()

        return type.__new__(cls, name, bases, namespace)


class Variable(object):
    _creation_counter = 0  # For sorting, incremented by `__init__`

    def __init__(self, name, type=Type, required=True, help_text=""):
        self.position = Variable._creation_counter
        Variable._creation_counter += 1
        if callable(type):
            type = type()
        assert isinstance(type, Type), "`type` must be a Type instance"
        assert isinstance(required, bool), "`required` must be a bool (it's %r)" % required
        self.name = name
        self.type = type
        self.required = bool(required)
        self.help_text = help_text

    def get_matching_types(self, variable_dict):
        return set(
            name
            for name, variable
            in six.iteritems(variable_dict)
            if self.type.is_coercible_from(variable.type)
        )


class Binding(Variable):
    def __init__(self,
                 name, type=Type, required=False,
                 help_text="", constant_use=ConstantUse.VARIABLE_ONLY, default=None):
        super(Binding, self).__init__(name=name, type=type, required=required, help_text=help_text)
        self.constant_use = constant_use
        self.default = default

    @property
    def accepts_any_type(self):
        return (not self.type.identifier)

    @property
    def allow_constant(self):
        return self.constant_use in (ConstantUse.CONSTANT_ONLY, ConstantUse.VARIABLE_OR_CONSTANT)

    @property
    def allow_variable(self):
        return self.constant_use in (ConstantUse.VARIABLE_ONLY, ConstantUse.VARIABLE_OR_CONSTANT)

    def get_value(self, context, bind_data):
        if bind_data:
            assert isinstance(bind_data, dict), "invalid bind data"
            if self.allow_constant and "constant" in bind_data:
                return self.type.unserialize(bind_data["constant"])
            if self.allow_variable and "variable" in bind_data:
                return context.get(bind_data["variable"], self.default)

        return self.default


class TemplatedBinding(Binding):
    def __init__(self, *args, **kwargs):
        super(TemplatedBinding, self).__init__(*args, **kwargs)
        if self.allow_variable:
            raise ValueError("TemplatedBindings may not allow variable binding for security reasons")

    def get_value(self, context, bind_data):
        value = super(TemplatedBinding, self).get_value(context, bind_data)
        try:
            return render_in_context(context, value)
        except TemplateError:
            # Return the unrendered value if there was template trouble.
            return value


class Base(six.with_metaclass(BaseMetaclass)):
    identifier = None
    name = None
    description = None
    variables = {}  # Filled by the metaclass
    bindings = {}  # Filled by the metaclass
    provide_category = None

    @classmethod
    def class_for_identifier(cls, identifier):
        return get_identifier_to_object_map(cls.provide_category).get(identifier)


class Event(Base):
    provide_category = "notify_event"
    identifier = None

    #: The name of the variable to be used as the log target for this event.
    #:
    #: The target variable must have an `add_log_entry` method.
    log_target_variable = None

    def __init__(self, **variable_values):
        if not self.identifier:
            raise ValueError("Attempting to instantiate identifierless event")
        self.variable_values = {}
        self.load_variables(variable_values)

    @property
    def log_target(self):
        return self.variable_values.get(self.log_target_variable)

    def load_variables(self, variable_values):
        for key in sorted(variable_values.keys()):
            variable = self.variables.get(key)
            if not variable:
                raise ValueError("Unknown variable %r for event %s" % (key, self.identifier))
            self.variable_values[key] = variable.type.unserialize(variable_values.pop(key))

        for name, variable in six.iteritems(self.variables):
            if variable.required and name not in self.variable_values:
                raise ValueError("Required variable %r missing for event %s" % (name, self.identifier))

    def run(self):
        from .runner import run_event
        run_event(event=self)


class ScriptItem(Base):
    provide_category = None

    def __init__(self, data, validate=True):
        if not self.identifier:  # pragma: no cover
            raise ValueError("Attempting to initialize %s without identifier: %r" % (self.__class__.__name__, self))
        self.data = data
        if validate:
            self.verify_bindings()

    def verify_bindings(self):
        unbound = set()
        for name, binding in six.iteritems(self.bindings):
            if binding.required and name not in self.data:
                unbound.add(name)
        if unbound:
            raise ValueError("Bindings unbound for %r: %r" % (self.identifier, unbound))

    def get_value(self, context, binding_name):
        """
        Get the actual value of a binding from the given script context.

        :param context: Script Context
        :type context: shoop.notify.script.Context
        :param binding_name: Binding name.
        :type binding_name: str
        :return: The variable value
        """
        binding = self.bindings[binding_name]
        bind_data = self.data.get(binding_name)
        return binding.get_value(context, bind_data)

    def get_values(self, context):
        """
        Get all binding values in a dict.

        :param context: Script Context
        :type context: shoop.notify.script.Context
        :return: Dict of binding name -> value
        :rtype: dict[name, value]
        """
        return dict((binding_name, self.get_value(context, binding_name)) for binding_name in self.bindings)

    @classmethod
    def unserialize(cls, data, validate=True):
        data = data.copy()
        obj_cls = cls.class_for_identifier(data.pop("identifier"))
        assert issubclass(obj_cls, cls)
        return obj_cls(data, validate=validate)

    def serialize(self):
        data = dict(identifier=self.identifier)
        data.update(**self.data)
        return data

    def __eq__(self, other):
        return self.identifier == other.identifier and self.data == other.data

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def get_ui_info_map(cls):
        map = {}
        for identifier, object in six.iteritems(get_identifier_to_object_map(cls.provide_category)):
            map[identifier] = {
                "identifier": str(identifier),
                "name": force_text(object.name),
                "description": force_text(getattr(object, "description", None) or ""),
            }
        return map


class Condition(ScriptItem):
    provide_category = "notify_condition"

    @abstractmethod
    def test(self, context):
        return False  # pragma: no cover


class Action(ScriptItem):
    provide_category = "notify_action"
    template_use = TemplateUse.NONE
    template_fields = {}

    @abstractmethod
    def execute(self, context):
        """
        :param context: Script Context
        :type context: shoop.notify.script.Context
        """
        pass  # pragma: no cover

    def get_template(self, context):
        """
        Get this action's template instance, bound in the
        context.

        :rtype: shoop.notify.template.Template
        """

        data = self.data.get("template_data")
        if not data:
            raise ValueError("No template data in action")
        return Template(context, data=data)

    def get_template_values(self, context, language_preferences=()):
        """
        Render this Action's template with data from the given context.

        :param context: Script Context
        :type context: shoop.notify.script.Context
        :param language_preferences:
            Language preference list.
            The first language in the template to have values for
            all fields will be used.
            Has no effect for UNILINGUAL template_use.
        :type language_preferences: list[str]
        :return: Dict of field name -> rendered template text.
        :rtype: dict[str, str]|None
        """

        if self.template_use == TemplateUse.NONE:
            raise ValueError("Attempting to `get_template_values` on an action with no template use")

        template = self.get_template(context)
        fields = self.template_fields.keys()

        if self.template_use == TemplateUse.UNILINGUAL:
            language_preferences = [UNILINGUAL_TEMPLATE_LANGUAGE]

        return template.render_first_match(language_preferences, fields)
