/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const m = require("mithril");
const _ = require("lodash");
const {dropzoneConfig} = require("../util/dragDrop");
const folderActions = require("../actions/folderActions");

export default function(ctrl) {
    const currentFolderId = ctrl.currentFolderId();
    const folderPath = ctrl.currentFolderPath();
    const idsToCurrent = _.pluck(folderPath, "id");

    function clickFolder(event, folderId) {
        ctrl.setFolder(folderId);
        event.preventDefault();
        return false;
    }

    function walk(folder) {
        if (folder.id === undefined) {
            return;
        }
        const inPath = (idsToCurrent.indexOf(folder.id) > -1);
        const isCurrent = (currentFolderId === folder.id);
        const nameLink = m("a", {href: "#", onclick: _.partialRight(clickFolder, folder.id)}, [
            (inPath ? m("i.caret-icon.fa.fa-caret-down") : m("i.caret-icon.fa.fa-caret-right")),
            (isCurrent ? m("i.folder-icon.fa.fa-folder-open") : m("i.folder-icon.fa.fa-folder")),
            m("span.name", folder.name)
        ]);
        const childLis = (inPath ? _.map(folder.children, walk) : []);
        if (isCurrent) {
            childLis.push(m("li.new-folder-item", {key: "new-folder"}, m("a", {
                href: "#",
                onclick: _.bind(folderActions.promptCreateFolder, null, ctrl, folder.id),
            }, m("i.fa.fa-plus"), " New folder")));
        }
        const className = _({
            "current": isCurrent,
            "in-path": inPath,
            "has-children": (folder.children.length > 0),
            "fd-zone": true
        }).pick(_.identity).keys().join(" ");
        return m("li",
            {
                "key": folder.id,
                "className": className,
                "data-folder-id": folder.id,
                "config": dropzoneConfig(ctrl)
            },
            [nameLink, (childLis && childLis.length ? m("ul", childLis) : null)]
        );
    }

    return m("ul", walk(ctrl.rootFolder()));
};
