# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest
from django.core.urlresolvers import reverse

from shuup import configuration
from shuup.apps.provides import override_provides
from shuup.front.apps.registration.notify_events import (
    RegistrationReceivedEmailScriptTemplate
)
from shuup.front.notify_script_templates.generics import (
    OrderConfirmationEmailScriptTemplate, PaymentCreatedEmailScriptTemplate,
    RefundCreatedEmailScriptTemplate, ShipmentCreatedEmailScriptTemplate,
    ShipmentDeletedEmailScriptTemplate
)
from shuup.notify.models import Script
from shuup.simple_supplier.notify_script_template import (
    StockLimitEmailScriptTemplate
)
from shuup.testing.browser_utils import (
    click_element, move_to_element, wait_until_condition
)
from shuup.testing.notify_script_templates import DummyScriptTemplate
from shuup.testing.browser_utils import initialize_admin_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


def initialize(browser, live_server, settings):
    initialize_admin_browser_test(browser, live_server, settings)


def post_initialize():
    """
    Does some post initialization for notify tests

    This since straight after `initialize_admin_browser_test`
    DB seems to be randomly locked and we want to wait
    until we perform these post procedures.
    """
    Script.objects.all().delete()


@pytest.mark.browser
@pytest.mark.djangodb
@pytest.mark.django_db
@pytest.mark.parametrize("script_template_cls", [
    OrderConfirmationEmailScriptTemplate,
    PaymentCreatedEmailScriptTemplate,
    RefundCreatedEmailScriptTemplate,
    ShipmentCreatedEmailScriptTemplate,
    ShipmentDeletedEmailScriptTemplate,
    RegistrationReceivedEmailScriptTemplate
])
def test_generic_script_template(browser, admin_user, live_server, settings, script_template_cls):
    initialize(browser, live_server, settings)

    url = reverse("shuup_admin:notify.script.list")
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(".shuup-toolbar a.btn.btn-default"))
    post_initialize()

    # find the button to load from template
    browser.find_by_css(".shuup-toolbar a.btn.btn-default").first.click()

    identifier = script_template_cls.identifier
    form_id = "form-" + identifier
    button_id = "#{} button.btn.btn-success".format(form_id)
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(button_id))
    click_element(browser, button_id)

    config_url = reverse("shuup_admin:notify.script-template-config", kwargs={"id": identifier})
    wait_until_condition(browser, lambda b: b.url.endswith(config_url), timeout=15)
    wait_until_condition(browser, lambda b: b.is_text_present("Configure the Script Template"))

    # click to create the script
    browser.execute_script("""
        $(document).ready(function(){
            $('#lang-en .summernote-editor').summernote('editor.insertText', 'NEW CONTENT');
        });
    """)
    browser.find_by_id("id_en-subject").fill("custom subject!")
    browser.find_by_css("form button.btn.btn-lg.btn-primary").first.click()

    wait_until_condition(browser, lambda b: b.url.endswith(reverse("shuup_admin:notify.script.list")))

    script = Script.objects.first()
    serialized_steps = script.get_serialized_steps()

    assert len(serialized_steps) == 1
    assert len(serialized_steps[0]["actions"]) == 1
    assert len(serialized_steps[0]["conditions"]) == 0
    assert serialized_steps[0]["actions"][0]["recipient"]["variable"] == "customer_email"
    assert serialized_steps[0]["actions"][0]["template_data"]["en"]["subject"] == "custom subject!"
    assert "NEW CONTENT" in serialized_steps[0]["actions"][0]["template_data"]["en"]["body"]


@pytest.mark.browser
@pytest.mark.djangodb
@pytest.mark.parametrize("script_template_cls", [
    OrderConfirmationEmailScriptTemplate,
    PaymentCreatedEmailScriptTemplate,
    RefundCreatedEmailScriptTemplate,
    ShipmentCreatedEmailScriptTemplate,
    ShipmentDeletedEmailScriptTemplate,
    RegistrationReceivedEmailScriptTemplate
])
def test_generic_custom_email_script_template(browser, admin_user, live_server, settings, script_template_cls):
    initialize(browser, live_server, settings)

    url = reverse("shuup_admin:notify.script.list")
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(".shuup-toolbar a.btn.btn-default"))
    post_initialize()

    # find the button to load from template
    browser.find_by_css(".shuup-toolbar a.btn.btn-default").first.click()

    identifier = script_template_cls.identifier
    form_id = "form-" + identifier
    button_id = "#{} button.btn.btn-success".format(form_id)
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(button_id))
    click_element(browser, button_id)

    config_url = reverse("shuup_admin:notify.script-template-config", kwargs={"id": identifier})
    wait_until_condition(browser, lambda b: b.url.endswith(config_url), timeout=15)
    wait_until_condition(browser, lambda b: b.is_text_present("Configure the Script Template"))

    browser.execute_script("""
        $(document).ready(function(){
            // EN
            $("#id_en-subject").val("custom subject!");
            $('#lang-en .summernote-editor').summernote('editor.insertText', 'Hi');

            // FINNISH
            $('.nav.nav-tabs a[href="#lang-fi"]').tab('show');
            $("#id_fi-subject").val("FINNISH subject!");
            $('#lang-fi .summernote-editor').summernote('editor.insertText', 'Hi Finland!');
        });
    """)

    # fill form
    move_to_element(browser, "#id_base-send_to")
    browser.select('base-send_to', 'other')
    browser.find_by_id("id_base-recipient").fill("other@shuup.com")
    browser.find_by_css("form button.btn.btn-lg.btn-primary").first.click()

    wait_until_condition(browser, lambda b: b.url.endswith(reverse("shuup_admin:notify.script.list")))

    script = Script.objects.first()
    serialized_steps = script.get_serialized_steps()

    assert len(serialized_steps) == 1
    assert len(serialized_steps[0]["actions"]) == 1
    assert len(serialized_steps[0]["conditions"]) == 0
    assert serialized_steps[0]["actions"][0]["recipient"]["constant"] == "other@shuup.com"

    assert serialized_steps[0]["actions"][0]["template_data"]["en"]["subject"] == "custom subject!"
    assert "Hi" in serialized_steps[0]["actions"][0]["template_data"]["en"]["body"]
    assert serialized_steps[0]["actions"][0]["template_data"]["fi"]["subject"] == "FINNISH subject!"
    assert "Hi Finland!" in serialized_steps[0]["actions"][0]["template_data"]["fi"]["body"]

    # edit the script
    url = reverse("shuup_admin:notify.script.edit", kwargs={"pk": script.pk})
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda b: b.is_text_present("Edit Script Information"))

    # find the button to edit the script content through template editor
    browser.find_by_css(".shuup-toolbar a.btn.btn-primary").last.click()
    edit_url = reverse("shuup_admin:notify.script-template-edit", kwargs={"pk": script.pk})
    wait_until_condition(browser, lambda b: b.url.endswith(edit_url))
    wait_until_condition(browser, lambda b: b.is_text_present("Configure the Script Template"))

    # fill form
    browser.execute_script("""
        $(document).ready(function(){
            $('#lang-en .summernote-editor').summernote('editor.insertText', 'Changed');
        });
    """)
    browser.find_by_id("id_en-subject").fill("changed subject!")

    move_to_element(browser, "#id_base-send_to")
    browser.select('base-send_to', 'customer')
    browser.find_by_css("form button.btn.btn-lg.btn-primary").first.click()

    # hit save
    wait_until_condition(browser, lambda b: b.url.endswith(reverse("shuup_admin:notify.script.list")))

    script = Script.objects.first()
    serialized_steps = script.get_serialized_steps()

    assert len(serialized_steps) == 1
    assert len(serialized_steps[0]["actions"]) == 1
    assert len(serialized_steps[0]["conditions"]) == 0
    assert serialized_steps[0]["actions"][0]["recipient"]["variable"] == "customer_email"

    assert serialized_steps[0]["actions"][0]["template_data"]["en"]["subject"] == "changed subject!"
    assert "Changed" in serialized_steps[0]["actions"][0]["template_data"]["en"]["body"]


@pytest.mark.browser
@pytest.mark.djangodb
def test_stock_alert_limit_script_template(browser, admin_user, live_server, settings):
    initialize(browser, live_server, settings)

    url = reverse("shuup_admin:notify.script.list")
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(".shuup-toolbar a.btn.btn-default"))
    post_initialize()

    # find the button to load from template
    browser.find_by_css(".shuup-toolbar a.btn.btn-default").first.click()

    identifier = StockLimitEmailScriptTemplate.identifier
    form_id = "form-" + identifier
    wait_until_condition(browser, lambda x: x.is_element_present_by_id(form_id))

    button_selector = "#{} button.btn.btn-success".format(form_id)
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(button_selector))
    click_element(browser, button_selector)

    config_url = reverse("shuup_admin:notify.script-template-config", kwargs={"id": identifier})
    wait_until_condition(browser, lambda b: b.url.endswith(config_url))
    wait_until_condition(browser, lambda b: b.is_text_present("Configure the Script Template"))

    subject = "custom subject!"
    recipient = "email@shuup.com"
    browser.find_by_id("id_en-subject").fill(subject)
    browser.find_by_id("id_base-recipient").fill(recipient)
    browser.find_by_css("form button.btn.btn-lg.btn-primary").first.click()

    wait_until_condition(browser, lambda b: b.url.endswith(reverse("shuup_admin:notify.script.list")))

    script = Script.objects.first()
    serialized_steps = script.get_serialized_steps()

    assert len(serialized_steps) == 1
    assert len(serialized_steps[0]["actions"]) == 1
    assert serialized_steps[0]["actions"][0]["recipient"]["constant"] == recipient
    assert len(serialized_steps[0]["conditions"]) == 1
    assert serialized_steps[0]["conditions"][0]["v1"]["variable"] == "dispatched_last_24hs"
    assert not serialized_steps[0]["conditions"][0]["v2"]["constant"]
    assert serialized_steps[0]["actions"][0]["template_data"]["en"]["subject"] == subject

    # edit the script
    url = reverse("shuup_admin:notify.script.edit", kwargs={"pk": script.pk})
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, lambda b: b.is_text_present("Edit Script Information"))

    # find the button to edit the script content through template editor
    browser.find_by_css(".shuup-toolbar a.btn.btn-primary").last.click()
    edit_url = reverse("shuup_admin:notify.script-template-edit", kwargs={"pk": script.pk})
    wait_until_condition(browser, lambda b: b.url.endswith(edit_url))
    wait_until_condition(browser, lambda b: b.is_text_present("Configure the Script Template"))

    # fill form
    subject = "changed sub"
    recipient = "changed.email@shuup.com"
    browser.find_by_id("id_en-subject").fill(subject)
    browser.find_by_id("id_base-recipient").fill(recipient)
    browser.uncheck("base-last24hrs")
    browser.find_by_css("form button.btn.btn-lg.btn-primary").first.click()

    # hit save
    wait_until_condition(browser, lambda b: b.url.endswith(reverse("shuup_admin:notify.script.list")))

    script = Script.objects.first()
    serialized_steps = script.get_serialized_steps()

    assert len(serialized_steps) == 1
    assert len(serialized_steps[0]["actions"]) == 1
    assert serialized_steps[0]["actions"][0]["recipient"]["constant"] == recipient
    assert len(serialized_steps[0]["conditions"]) == 0
    assert serialized_steps[0]["actions"][0]["template_data"]["en"]["subject"] == subject


@pytest.mark.browser
@pytest.mark.djangodb
def test_dummy_script_template(browser, admin_user, live_server, settings):
    initialize(browser, live_server, settings)

    with override_provides("notify_script_template", ["shuup.testing.notify_script_templates:DummyScriptTemplate"]):
        url = reverse("shuup_admin:notify.script.list")
        browser.visit("%s%s" % (live_server, url))
        wait_until_condition(browser, lambda x: x.is_element_present_by_css(".shuup-toolbar a.btn.btn-default"))
        post_initialize()

        # find the button to load from template
        browser.find_by_css(".shuup-toolbar a.btn.btn-default").first.click()

        identifier = DummyScriptTemplate.identifier
        form_id = "form-" + identifier
        wait_until_condition(browser, lambda x: x.is_element_present_by_id(form_id))

        btn_create_css = "#{} button.btn.btn-success".format(form_id)
        wait_until_condition(browser, lambda x: x.is_element_present_by_css(btn_create_css))
        click_element(browser, btn_create_css)

        wait_until_condition(browser, lambda b: b.url.endswith(reverse("shuup_admin:notify.script.list")))

        script = Script.objects.first()
        serialized_steps = script.get_serialized_steps()
        assert len(serialized_steps) == 1
        assert len(serialized_steps[0]["actions"]) == 0
        assert len(serialized_steps[0]["conditions"]) == 1
        assert serialized_steps[0]["conditions"][0]["v1"]["constant"]
        assert not serialized_steps[0]["conditions"][0]["v2"]["constant"]

        # edit the script
        url = reverse("shuup_admin:notify.script.edit", kwargs={"pk": script.pk})
        browser.visit("%s%s" % (live_server, url))
        wait_until_condition(browser, lambda b: b.is_text_present("Edit Script Information"))

        # should exist only a single button to edit the script content
        assert len(browser.find_by_css(".shuup-toolbar a.btn.btn-primary")) == 1
        assert "Edit Script Contents" in browser.find_by_css(".shuup-toolbar a.btn.btn-primary").first.text
