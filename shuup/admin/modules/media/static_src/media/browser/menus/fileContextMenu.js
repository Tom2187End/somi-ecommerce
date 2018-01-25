/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const fileActions = require("../actions/fileActions");
const menuItem = require("./menuItem");

export default function(controller, file) {
    return function() {
        return [
            menuItem(gettext("Rename file"), () => {
                fileActions.promptRenameFile(controller, file);
            }, {disabled: controller.isMenuDisabled("rename")}),
            menuItem(gettext("Delete file"), () => {
                fileActions.promptDeleteFile(controller, file);
            }, {disabled: controller.isMenuDisabled("delete")})
        ];
    };
}
