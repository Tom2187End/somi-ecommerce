/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const m = require("mithril");
const button = require("./button");
const _ = require("lodash");
const emptyFolderView = require("./emptyFolderView");
const gridFileView = require("./gridFileView");
const listFileView = require("./listFileView");
const responsiveUploadHint = require("./responsiveUploadHint");
const {dropzoneConfig} = require("../util/dragDrop");
const images = require("./images");

function sortBySpec(data, sortString) {
    sortString = /^([+-])(.+)$/.exec(sortString || "+name");
    data = _.sortBy(data || [], sortString[2]);
    if (sortString[1] === "-") {
        data = data.reverse();
    }
    return data;
}

export default function folderView(ctrl) {
    const folderData = ctrl.folderData();
    const viewModeGroup = m("div.btn-group.btn-group-sm.icons", [
        button(ctrl.viewMode, "grid", m("i.fa.fa-th"), "Grid"),
        button(ctrl.viewMode, "list", m("i.fa.fa-th-list"), "List")
    ]);
    const sortGroup = m("div.btn-group.btn-group-sm", [
        button(ctrl.sortMode, "+name", "A-Z"),
        button(ctrl.sortMode, "-name", "Z-A"),
        button(ctrl.sortMode, "+date", gettext("Oldest first")),
        button(ctrl.sortMode, "-date", gettext("Newest first")),
        button(ctrl.sortMode, "+size", gettext("Smallest first")),
        button(ctrl.sortMode, "-size", gettext("Largest first"))
    ]);
    var toolbar = m("div.btn-toolbar", [viewModeGroup, sortGroup]);
    const files = sortBySpec(folderData.files || [], ctrl.sortMode());
    const folders = sortBySpec(folderData.folders || [], ctrl.sortMode());
    var contents = null, uploadHint = null;
    if (folders.length === 0 && files.length === 0) {
        contents = emptyFolderView(ctrl, folderData);
        toolbar = null;
    } else {
        switch (ctrl.viewMode()) {
            case "grid":
                contents = gridFileView(ctrl, folders, files);
                break;
            case "list":
                contents = listFileView(ctrl, folders, files);
                break;
        }
        uploadHint = m("div.upload-hint", responsiveUploadHint);
    }
    const container = m("div.folder-contents.fd-zone", {
        "data-folder-id": folderData.id,
        config: dropzoneConfig(ctrl),
    }, [
        contents,
        uploadHint,
        m("div.upload-indicator", [
            m("div.image",
                m("img", {src: images.uploadIndicator})
            ),
            m("div.text", [
                m.trust(gettext("Drop your files here"))
            ])
        ])
    ]);

    return m("div.folder-view", [toolbar, container]);
}
