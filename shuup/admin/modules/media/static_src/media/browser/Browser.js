/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

const _ = require("lodash");
const m = require("mithril");
const BrowserView = require("./BrowserView");
const dragDrop = require("./util/dragDrop");
const FileUpload = require("./FileUpload");
const menuManager = require("./util/menuManager");
const folderContextMenu = require("./menus/folderContextMenu");

var controller = null;

export function init(config={}) {
    if (controller !== null) {
        return;
    }
    controller = m.mount(document.getElementById("BrowserView"), {
        view: BrowserView.view,
        controller: _.partial(BrowserView.controller, config)
    });
    controller.navigateByHash();
    controller.reloadFolderTree();

    dragDrop.disableIntraPageDragDrop();
}

export function openFolderContextMenu(event) {
    const button = event.target;
    menuManager.open(button, folderContextMenu(controller));
}

export function setupUploadButton(element) {
    const input = document.createElement("input");
    input.type = "file";
    input.multiple = true;
    input.style.display = "none";
    input.addEventListener("change", function(event) {
        FileUpload.enqueueMultiple(controller.getUploadUrl(), event.target.files);
        FileUpload.addQueueCompletionCallback(() => { controller.reloadFolderContentsSoon(); });
        FileUpload.processQueue();
    });
    document.body.appendChild(input);
    element.addEventListener("click", function(event) {
        input.click();
        event.preventDefault();
    }, false);
}
