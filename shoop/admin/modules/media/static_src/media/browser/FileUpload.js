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
const remote = require("./util/remote");

const queue = [];
const queueCompleteCallbacks = [];
var queueStatusDiv = null;

function queueView() {
    var className = "empty";
    if(queue.length >= 0) {
        className = (
            _.all(queue, (file) => (file.status === "done" || file.status === "error")) ?
                "done" : "busy"
        );
    }

    return m("div.queue-view." + className, _.map(queue, (file) => {
        return m("div.queue-file." + file.status, [
            m("div.qf-name", file.name),
            m("div.qf-progress", {style: "width: " + (file.progress || 0) + "%"})
        ]);
    }));
}

function updateQueueView() {
    if(queueStatusDiv === null) {
        if(queue.length === 0) {
            return;  // Don't bother setting up the div if we're not doing anything actually
        }
        queueStatusDiv = document.createElement("div");
        queueStatusDiv.id = "queue-status-ctr";
        document.body.appendChild(queueStatusDiv);
        // Yes, we're throwing away the ctrl instance; we don't need it
        // and eslint would kvetch about it otherwise :)
        m.mount(queueStatusDiv, {view: queueView, controller: _.noop});
    }
    m.redraw();  // XXX: It would be nice if we could redraw only one Mithril view...
}

const updateQueueViewSoon = _.debounce(updateQueueView, 50);

function handleFileXhrComplete(xhr, file, error) {
    if (xhr.status >= 400) {
        error = true;
    }
    if (error) {
        file.status = "error";

    } else {
        file.status = "done";
        file.progress = 100;
    }
    setTimeout(processQueue, 50);  // Continue soon.
    var messageText = null;
    try {
        const responseJson = JSON.parse(xhr.responseText);
        if (responseJson && responseJson.message) {
            messageText = responseJson.message;
        }
    } catch (e) {
        // invalid JSON? pffff.
        console.log(e); // eslint-disable-line
    }
    if (window.Messages) {
        if (error && !messageText) {
            messageText = "Unexpected error while uploading files.";
        }
        const response = {
            error: (error ? "Error: " + file.name + ": " + messageText : null),
            message: (!error ? messageText || "Uploaded: " + file.name : null)
        };
        remote.handleResponseMessages(response);
    }
}

function beginUpload(file) {
    if (file.status !== "new") {  // Already uploaded? Huh.
        return false;
    }
    file.progress = 0;
    file.status = "uploading";

    const formData = new FormData();
    formData.append("file", file.nativeFile);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", file.url);
    xhr.setRequestHeader("X-CSRFToken", window.ShoopAdminConfig.csrf);
    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) {
            // Ready state 4:
            // .. The data transfer has been completed or something went
            // .. wrong during the transfer (e.g. infinite redirects).
            // That's the only case we want to handle, so return otherwise.
            return;
        }
        handleFileXhrComplete(xhr, file, false);
        updateQueueViewSoon();
    };
    xhr.onerror = function() {
        handleFileXhrComplete(xhr, file, true);
        updateQueueViewSoon();
    };
    xhr.upload.onprogress = function(event) {
        if (event.lengthComputable) {
            file.progress = (event.loaded / event.total);
        } else {
            file.progress = file.progress + (100 - file.progress) / 2;
        }
        updateQueueViewSoon();
    };
    xhr.send(formData);
}

export function enqueue(uploadUrl, file) {
    queue.push({
        url: uploadUrl,
        name: file.name,
        nativeFile: file,
        status: "new",  // "new"/"uploading"/"error"/"done"
        progress: 0
    });
}

export function enqueueMultiple(uploadUrl, files) {
    _.each(files, (file) => {
        enqueue(uploadUrl, file);
    });
}

export function addQueueCompletionCallback(callback) {
    queueCompleteCallbacks.push(callback);
}

export function processQueue() {
    if(_.any(queue, (file) => file.status === "uploading")) {
        return;  // Don't allow uploading multiple files simultaneously though...
    }
    const nextFile = _.detect(queue, (file) => (file.status === "new"));
    updateQueueViewSoon();
    if (nextFile) {
        beginUpload(nextFile);
    } else {
        while (queueCompleteCallbacks.length) {
            const cb = queueCompleteCallbacks.shift();
            cb();
        }
    }
}
