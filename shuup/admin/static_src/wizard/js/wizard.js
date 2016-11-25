/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
(function($) {
    $.fn.wizard = function(config={}) {
        let $navItems = this.find(".wizard-nav li");
        let $panes = this.find(".wizard-pane");
        let $activeNavItem = $navItems.find(".active");
        let $activeWizardPane = $panes.filter(".active");

        function isLastPane(){
            return $panes.index($activeWizardPane) == $panes.length - 1;
        }

        function getButton(text, name, disable, classes, tooltip) {
            return (
                '<button name="' + name + '"' +
                         'class="btn btn-lg ' + classes + '" ' + (disable? "disabled":"") +
                         (tooltip? "data-toggle='tooltip' data-placement='bottom' title='" + tooltip + "'": "") +
                         '>' +
                    text +
                '</button>'
            );
        }

        function addActionBarToActivePane() {
            $panes.find(".action-bar").remove();
            let disablePrevious = false;
            let disableNext = false;
            if($panes.index($activeWizardPane) === 0) {
                disablePrevious = true;
            }
            if(isLastPane() && !config.redirectOnLastPane) {
                disableNext = true;
            }

            $activeWizardPane.append(
                '<div class="action-bar">' +
                    '<div class="clearfix">' +
                        getButton(gettext("Previous"), "previous", disablePrevious, "btn-primary pull-left " + (config.hidePrevious? "hidden":"")) +
                        getButton(isLastPane() ? gettext("Finish") : gettext("Next"), "next", disableNext, "btn-primary pull-right") +
                    '</div>' +
                    (config.skip?
                    '<div class="clearfix">' +
                        getButton(gettext("Skip Setup"), "skip", false, "btn-default pull-right", config.skipTooltip) +
                    '</div>': '') +
                '</div>'
            );
            $activeWizardPane.find('[data-toggle="tooltip"]').tooltip();
        }

        function switchToPane(index) {
            $navItems.removeClass("active");
            $panes.removeClass("active");
            $activeNavItem = $navItems.eq(index);
            $activeWizardPane = $panes.eq(index);
            $activeNavItem.addClass("active");
            $activeWizardPane.addClass("active");

            addActionBarToActivePane();
        }

        function next() {
            switchToPane($panes.index($activeWizardPane) + 1);
        }

        function previous() {
            switchToPane($panes.index($activeWizardPane) - 1);
        }

        function submit() {
            let $form = $activeWizardPane.find("form");
            clearErrors($form);
            return $.ajax({method: "POST", traditional: true, data: serializeForm($form)});
        }

        var pubFuncs = {next, previous, submit};

        if(config in pubFuncs){
            return pubFuncs[config]();
        } else if($.isNumeric(config)){
            switchToPane(config);
        } else {
            this.on("click", "button[name='next']", () => {
                this.find("button[name='next']").prepend('<i class="fa fa-spinner fa-pulse fa-fw"></i>');
                if(config.next) {
                    config.next($activeWizardPane);
                } else {
                    submit().done(() => {
                        if(config.redirectOnLastPane && isLastPane()){
                            window.location = config.redirectOnLastPane;
                        } else {
                            next();
                        }
                    }).fail((err) => {
                        this.find("i.fa.fa-spinner").remove();
                        renderFormErrors($activeWizardPane.find("form"), err.responseJSON);
                    });
                }
            });

            this.on("click", "button[name='previous']", () => {
                this.find("button[name='previous']").prepend('<i class="fa fa-spinner fa-pulse fa-fw"></i>');
                if(config.previous) {
                    config.previous($activeWizardPane);
                } else {
                    previous();
                }
            });

            this.on("click", "button[name='skip']", () => {
                config.skip();
            });
            switchToPane(0);
        }
        return this;
    };
}(jQuery));
