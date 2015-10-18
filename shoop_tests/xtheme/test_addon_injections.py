# -*- coding: utf-8 -*-
import pytest

from shoop.apps.provides import override_provides
from shoop.xtheme.theme import override_current_theme_class
from shoop.xtheme.resources import InlineScriptResource, add_resource
from shoop_tests.xtheme.utils import get_jinja2_engine, get_request


def add_test_injection(context, content):
    add_resource(context, "body_end", InlineScriptResource("window.injectedFromAddon=true;"))


@pytest.mark.django_db
def test_simple_addon_injection():
    request = get_request(edit=False)
    jeng = get_jinja2_engine()
    template = jeng.get_template("resinject.jinja")

    with override_current_theme_class():
        with override_provides(
                "xtheme_resource_injection", ["shoop_tests.xtheme.test_addon_injections:add_test_injection",]):
            # TestInjector should add alert to end of the body for every request
            output = template.render(request=request)
            head, body = output.split("</head>", 1)
            assert "window.injectedFromAddon=true;" in body
