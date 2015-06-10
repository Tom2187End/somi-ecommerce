/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    "use strict";
    /**
     * Return a Mithril module to create a navigator for the given navigatee form (jQuery object)
     */
    function getSectionNavigatorModule($navigateeForm) {
        let $sections = $navigateeForm.find(".content-block");

        let navigationListItems = _.compact(_.map($sections, function(section) {
            let $section = $(section);
            let $blockTitle = $section.find(".block-title");
            let titleText = $blockTitle.text();
            if (!titleText) return;
            if (!section.id) {
                section.id = _.kebabCase(titleText) + "-section";
            }

            return {
                el: section,
                id: section.id,
                title: titleText,
                iconClass: $blockTitle.find(".fa").attr("class")
            };
        }));

        if (!navigationListItems.length) {
            return null;
        }

        return {
            view: function view(ctrl) {
                var currentId = ctrl.currentItemId();
                return m("div.sidebar-list", ctrl.navigationListItems().map(function(item) {
                    return m(
                        "a.sidebar-list-item" + (item.id == currentId ? ".active" : ""),
                        {
                            key: item.id,
                            href: "#" + item.id,
                            onclick: function() {
                                ctrl.showSection(item);
                                return false;
                            }
                        },
                        [
                            (item.iconClass ? m("i", {className: item.iconClass}) : null),
                            item.title
                        ]
                    );
                }));
            },
            controller: function controller() {
                let ctrl = this;
                ctrl.showSection = function(section) {
                    $sections.hide();
                    let $visibleSection = $("#" + section.id);
                    $visibleSection.show();
                    ctrl.currentItemId(section.id);
                };
                ctrl.currentItemId = m.prop(null);
                ctrl.navigationListItems = m.prop(navigationListItems);
                ctrl.showSection(navigationListItems[0]);
            }
        };
    }
    function activateSectionNavigation($sectionNavigation) {
        if (!$sectionNavigation.length) return;
        let navigateeId = $sectionNavigation.data("navigatee");
        let $navigateeForm = $("#" + navigateeId);
        if (!$navigateeForm.length) return;
        m.mount($sectionNavigation[0], getSectionNavigatorModule($navigateeForm));
    }
    $(".section-navigation, #section-navigation").each(function() {
        activateSectionNavigation($(this));
    });
});
