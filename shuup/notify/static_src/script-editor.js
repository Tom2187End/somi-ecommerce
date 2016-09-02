/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
const style = require("style!css!autoprefixer!less!./script-editor.less");  // eslint-disable-line no-unused-vars
const cx = require("classnames");
const Messages = window.Messages;

var settings = {};
const names = {};
const infos = {};
var controller = null;
const optionLists = {};

function showSuccessAndError(data) {
    if (data.error) {
        Messages.enqueue({
            text: _.isString(data.error) ? data.error : gettext("An error occurred."),
            tags: "error"
        });
    }
    if (data.success) {
        Messages.enqueue({
            text: _.isString(data.success) ? data.success : gettext("Success."),
            tags: "success"
        });
    }
}

function apiRequest(command, data, options) {
    const request = _.extend({}, {"command": command}, data || {});
    const req = m.request(_.extend({
        method: "POST",
        url: settings.apiUrl,
        data: request,
        config: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", window.ShuupAdminConfig.csrf);
        }
    }, options));
    req.then(function(response) {
        showSuccessAndError(response);
    }, function() {
        Messages.enqueue({text: gettext("An unspecified error occurred."), tags: "error"});
    });
    return req;
}

function Controller() {
    const ctrl = this;
    ctrl.steps = m.prop([]);
    ctrl.currentItem = m.prop(null);
    ctrl.newStepItemModalInfo = m.prop(null);

    apiRequest("getData").then(function(data) {
        ctrl.steps(data.steps);
    });

    ctrl.removeStepItem = function(step, itemType, item) {
        const listName = itemType + "s";
        step[listName] = _.reject(step[listName], function(i) {
            return i === item;
        });
        if (ctrl.currentItem() === item) {
            ctrl.activateStepItem(null, null, null);
        }
    };

    ctrl.addStepItem = function(step, itemType, identifier, activateForEdit) {
        const item = {"identifier": identifier};
        const listName = itemType + "s";
        step[listName].push(item);
        if (activateForEdit) {
            ctrl.activateStepItem(step, itemType, item);
        }
    };
    ctrl.setStepItemEditorState = function(state) {
        if (state) {
            document.getElementById("step-item-wrapper").style.display = "block";
        } else {
            document.getElementById("step-item-wrapper").style.display = "none";
            document.getElementById("step-item-frame").src = "about:blank";
        }
    };
    ctrl.activateStepItem = function(step, itemType, item) {
        if (step && item) {
            ctrl.currentItem(item);
            const frm = _.extend(document.createElement("form"), {
                target: "step-item-frame",
                method: "POST",
                action: settings.itemEditorUrl
            });
            frm.appendChild(_.extend(document.createElement("input"), {
                name: "init_data",
                type: "hidden",
                value: JSON.stringify({
                    eventIdentifier: settings.eventIdentifier,
                    itemType: itemType,
                    data: item
                })
            }));
            document.body.appendChild(frm);
            frm.submit();
            ctrl.setStepItemEditorState(true);
        } else {
            ctrl.currentItem(null);
            ctrl.setStepItemEditorState(false);
        }
    };
    ctrl.receiveItemEditData = function(data) {
        const currentItem = ctrl.currentItem();
        if (!currentItem) {
            alert(gettext("Unexpected edit data received."));
            return;
        }
        m.startComputation();
        ctrl.currentItem(_.extend(currentItem, data));
        m.endComputation();
    };
    ctrl.saveState = function() {
        apiRequest("saveData", {
            steps: ctrl.steps()
        });

        // TODO: Handle errors here?
    };
    ctrl.deleteStep = function(step) {
        ctrl.steps(_.reject(ctrl.steps(), function(s) {
            return s === step;
        }));
    };
    ctrl.addNewStep = function() {
        const step = {
            actions: [],
            conditions: [],
            enabled: true,
            next: "continue",
            condOp: "and"
        };
        const steps = ctrl.steps();
        steps.push(step);
        ctrl.steps(steps);
    };
    ctrl.moveStep = function(step, delta) {
        const steps = ctrl.steps();
        const oldIndex = _.indexOf(steps, step);
        if (oldIndex === -1) {
            return false;
        }
        const newIndex = oldIndex + delta;
        steps.splice(newIndex, 0, steps.splice(oldIndex, 1)[0]);
        ctrl.steps(steps);
    };
    ctrl.promptForNewStepItem = function(step, itemType) {
        ctrl.newStepItemModalInfo({
            step: step,
            itemType: itemType,
            title: gettext("Add new") + " " + itemType
        });
    };
    ctrl.closeNewStepItemModal = function() {
        ctrl.newStepItemModalInfo(null);
    };
    ctrl.createNewStepItemFromModal = function(identifier) {
        const info = ctrl.newStepItemModalInfo();
        ctrl.closeNewStepItemModal();
        if (info === null) {
            return;
        }
        ctrl.addStepItem(info.step, info.itemType, identifier, true);
    };
}

function workflowItemList(ctrl, step, itemType) {
    const listName = itemType + "s";
    const nameMap = names[itemType];
    const items = step[listName];
    const list = m("ul.action-list", items.map(function(item) {
        const name = nameMap[item.identifier] || item.identifier;
        var tag = "li";
        const current = (ctrl.currentItem() === item);
        if (current) {
            tag += ".current";
        }
        return m(tag,
            [
                m("a", {
                    href: "#",
                    onclick: (!current ? _.partial(ctrl.activateStepItem, step, itemType, item) : null)
                }, name),
                " ",
                m("a.delete", {
                    href: "#", onclick: function() {
                        if (!confirm(gettext("Delete this item?\nThis can not be undone."))) {
                            return;
                        }
                        ctrl.removeStepItem(step, itemType, item);
                    }
                }, m("i.fa.fa-trash"))
            ]
        );
    }));
    return m("div", [
        list,
        m("div.action-new", [m("a.btn.btn-xs.btn-primary", {
            href: "#",
            onclick: _.partial(ctrl.promptForNewStepItem, step, itemType)
        }, m("i.fa.fa-plus"), " " + gettext("New") + " " + itemType)])
    ]);
}

function stepTableRows(ctrl) {
    return _.map(ctrl.steps(), function(step, index) {
        const condOpSelect = m("select", {
            value: step.cond_op,
            onchange: m.withAttr("value", function(value) {
                step.cond_op = value;  // eslint-disable-line camelcase
            })
        }, optionLists.condOps);
        const stepNextSelect = m("select", {
            value: step.next,
            onchange: m.withAttr("value", function(value) {
                step.next = value;
            })
        }, optionLists.stepNexts);

        return m("div", {
            className: cx("step", {disabled: !step.enabled}),
            key: step.id
        }, [
            m("div.step-buttons", [
                (index > 0 ? m("a", {
                    href: "#",
                    title: gettext("Move Up"),
                    onclick: _.partial(ctrl.moveStep, step, -1)
                }, m("i.fa.fa-caret-up")) : null),
                (index < ctrl.steps().length - 1 ? m("a", {
                    href: "#",
                    title: gettext("Move Down"),
                    onclick: _.partial(ctrl.moveStep, step, +1)
                }, m("i.fa.fa-caret-down")) : null),
                (step.enabled ?
                    m("a", {
                        href: "#", title: gettext("Disable"), onclick: function() {
                            step.enabled = false;
                        }
                    }, m("i.fa.fa-ban")) :
                    m("a", {
                        href: "#", title: gettext("Enable"), onclick: function() {
                            step.enabled = true;
                        }
                    }, m("i.fa.fa-check-circle"))
                ),
                m("a", {
                    href: "#", title: gettext("Delete"), onclick: function() {
                        if (confirm(gettext("Are you sure you wish to delete this step?"))) {
                            ctrl.deleteStep(step);
                        }
                    }
                }, m("i.fa.fa-trash"))
            ]),
            m("div.step-conds", [
                m("span.hint", interpolate(gettext("If %s of these conditions hold..."), [condOpSelect])),
                workflowItemList(ctrl, step, "condition")
            ]),
            m("div.step-actions", [
                m("span.hint", gettext("then execute these actions...")),
                workflowItemList(ctrl, step, "action")
            ]),
            m("div.step-next", [
                m("span.hint", gettext("and then...")),
                stepNextSelect
            ])
        ]);
    });
}

function renderNewStepItemModal(ctrl, modalInfo) {
    return m("div.new-step-item-modal-overlay", {onclick: ctrl.closeNewStepItemModal}, [
        m("div.new-step-item-modal", [
            m("div.title", modalInfo.title),
            m("div.item-options", _.map(_.sortBy(_.values(infos[modalInfo.itemType]), "name"), function(item) {
                return m("div.item-option", {onclick: _.partial(ctrl.createNewStepItemFromModal, item.identifier)}, [
                    m("div.item-name", item.name),
                    (item.description ? m("div.item-description", item.description) : null)
                ]);
            }))
        ])
    ]);
}

function view(ctrl) {
    var modal = null, modalInfo = null;
    if ((modalInfo = ctrl.newStepItemModalInfo()) !== null) {
        modal = renderNewStepItemModal(ctrl, modalInfo);
    }
    return m("div.step-list-wrapper", [
        m("div.steps", [
            stepTableRows(ctrl),
            m("hr.script-separator"),
            m(
                "a.new-step-link.btn.btn-info.btn-sm",
                {href: "#", onclick: ctrl.addNewStep},
                m("i.fa.fa-plus"), " " + gettext("New step")
            )
        ]),
        modal
    ]);
}

function generateItemOptions(nameMap) {
    return _.sortBy(_.map(nameMap, function(name, value) {
        return m("option", {value: value}, name);
    }), function(o) {
        return o.children[0].toLowerCase();
    });
}

function itemInfosToNameMap(itemInfos) {
    return _(itemInfos).map(function (itemInfo, identifier){ return [identifier, itemInfo.name]; }).zipObject().value();
}

function init(iSettings) {
    settings = _.extend({}, iSettings);
    infos.condition = settings.conditionInfos;
    infos.action = settings.actionInfos;
    names.condition = itemInfosToNameMap(infos.condition);
    names.action = itemInfosToNameMap(infos.action);
    optionLists.condOps = generateItemOptions(settings.condOps);
    optionLists.stepNexts = generateItemOptions(settings.stepNexts);

    controller = m.mount(document.getElementById("step-table-container"), {
        controller: Controller,
        view: view
    });
    window.addEventListener("message", function(event) {
        if (event.data.new_data) {
            controller.receiveItemEditData(event.data.new_data);
        }
    }, false);
}

function save() {
    controller.saveState();
}

module.exports.init = init;
module.exports.save = save;
module.exports.hideEditModal = function() {
    if (controller) {
        m.startComputation();
        controller.setStepItemEditorState(false);
        controller.activateStepItem(null);  // Deactivate the modal once data is received
        m.endComputation();
    }
};
