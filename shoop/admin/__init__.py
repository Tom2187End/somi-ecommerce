# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps import AppConfig
from shoop.apps.settings import validate_templates_configuration


class ShoopAdminAppConfig(AppConfig):
    name = "shoop.admin"
    verbose_name = "Shoop Admin"
    label = "shoop_admin"
    required_installed_apps = ["bootstrap3"]
    provides = {
        "admin_module": [
            "shoop.admin.modules.products:ProductModule",
            "shoop.admin.modules.product_types:ProductTypeModule",
            "shoop.admin.modules.media:MediaModule",
            "shoop.admin.modules.orders:OrderModule",
            "shoop.admin.modules.taxes:TaxModule",
            "shoop.admin.modules.categories:CategoryModule",
            "shoop.admin.modules.contacts:ContactModule",
            "shoop.admin.modules.contact_groups:ContactGroupModule",
            "shoop.admin.modules.users:UserModule",
            "shoop.admin.modules.methods:MethodModule",
            "shoop.admin.modules.attributes:AttributeModule",
            "shoop.admin.modules.demo:DemoModule"
        ]
    }

    def ready(self):
        validate_templates_configuration()


default_app_config = "shoop.admin.ShoopAdminAppConfig"
