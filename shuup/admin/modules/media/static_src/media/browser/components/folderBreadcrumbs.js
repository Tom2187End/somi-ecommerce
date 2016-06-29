/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const m = require("mithril");
const _ = require("lodash");
const folderClick = require("./folderClick");

export default function(ctrl) {
    const items = [];
    const folderPath = ctrl.currentFolderPath();
    _.each(folderPath, function(folder, index) {
        items.push(
            m("a.breadcrumb-link" + (index === folderPath.length - 1 ? ".current" : ""), {
                href: "#",
                key: folder.id,
                onclick: folderClick(ctrl, folder)
            }, folder.name)
        );
        items.push(m("i.fa.fa-angle-right"));
    });
    items.pop(); // pop last chevron
    items.unshift(m("i.fa.fa-folder-open.folder-icon"));
    return items;
}
