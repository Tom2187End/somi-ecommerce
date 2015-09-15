/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const _ = require("lodash");
const remote = require("../util/remote");

export function promptCreateFolder(controller, parentFolderId) {
    const name = prompt("New folder name?");
    if (!name) {  // Cancelled? :(
        return;
    }
    remote.post({action: "new_folder", parent: parentFolderId, name}).then(function(response) {
        remote.handleResponseMessages(response);
        const newCurrentFolder = 0 | response.folder.id;  // eslint-disable-line no-bitwise
        controller.setFolder(newCurrentFolder);
        controller.reloadFolderTree();
        controller.reloadFolderContents();
    });
}

export function promptCreateFolderHere(controller) {
    return promptCreateFolder(controller, controller.currentFolderId());
}

export function promptRenameCurrentFolder(controller) {
    const {id, name} = controller.folderData();
    const newName = _.trim(prompt("New folder name?", name) || "");
    if (newName && name !== newName) {
        remote.post({action: "rename_folder", id, name: newName}).then(function(response) {
            remote.handleResponseMessages(response);
            controller.reloadFolderTree();
            controller.reloadFolderContents();
        });
    }
}

export function promptDeleteCurrentFolder(controller) {
    const {id, name} = controller.folderData();
    if(confirm("Are you sure you want to delete the " + name + " folder?")) {
        remote.post({action: "delete_folder", id}).then(function(response) {
            remote.handleResponseMessages(response);
            const newCurrentFolder = 0 | response.newFolderId;  // eslint-disable-line no-bitwise
            controller.setFolder(newCurrentFolder);
            controller.reloadFolderTree();
            controller.reloadFolderContents();
        });
    }
}
