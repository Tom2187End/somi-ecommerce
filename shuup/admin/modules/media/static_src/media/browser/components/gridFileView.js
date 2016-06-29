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
const wrapFileLink = require("./wrapFileLink");
const folderLink = require("./folderLink");
const {dropzoneConfig} = require("../util/dragDrop");
const images = require("./images");
const menuManager = require("../util/menuManager");
const fileContextMenu = require("../menus/fileContextMenu");

export default function(ctrl, folders, files) {
    const folderItems = _.map(folders, function(folder) {
        return m("div.col-xs-6.col-md-4.col-lg-3.grid-folder.fd-zone", {
            key: "folder-" + folder.id,
            "data-folder-id": folder.id,
            config: dropzoneConfig(ctrl),
        }, [
            m("a.file-preview", {
                onclick: function() {
                    ctrl.setFolder(folder.id);
                    return false;
                },
                href: "#"
            }, m("i.fa.fa-folder-open.folder-icon")),
            m("div.file-name", folderLink(ctrl, folder))
        ]);
    });
    const fileItems = _.map(files, function(file) {
        return m(
            "div.col-xs-6.col-md-4.col-lg-3.grid-file",
            {
                key: file.id,
                draggable: true,
                ondragstart: (event) => {
                    event.stopPropagation();
                    event.dataTransfer.effectAllowed = "copyMove";
                    event.dataTransfer.setData("text", JSON.stringify({"fileId": file.id}));
                    try {
                        const dragIcon = document.createElement("img");
                        dragIcon.src = file.thumbnail || images.defaultThumbnail;
                        dragIcon.width = 100;
                        event.dataTransfer.setDragImage(dragIcon, 0, 0);
                    } catch (e) {
                        // This isn't a problem
                    }
                }
            },
            m("button.file-cog-btn.btn.btn-xs.btn-default", {
                key: "filecog",
                onclick: (event) => {
                    menuManager.open(event.currentTarget, fileContextMenu(ctrl, file));
                    event.preventDefault();
                }
            }, m("i.fa.fa-cog")),
            wrapFileLink(file, "a.file-preview", [
                m("img.img-responsive", {src: file.thumbnail || images.defaultThumbnail}),
                m("div.file-name", file.name)
            ])
        );
    });
    return m("div.row", folderItems.concat(fileItems));
}
