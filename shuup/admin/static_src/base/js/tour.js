/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
(function($) {
    function getAppChromeSteps(key) {
        if(key !== "home" && typeof(key) !== "undefined") {
            return [];
        }
        if($("#main-menu").position().left !== 0) {
            // don't show chrome tour on mobile
            return [];
        }
        let steps = [];
        steps = steps.concat([
            {
                title: gettext("Quick Links"),
                text: [
                    gettext("Quick Links to your most used features.")
                ],
                attachTo: "li a[data-target-id='quicklinks'] right"
            }, {
                title: gettext("Orders"),
                text: [
                    gettext("Track and filter your customers’ orders here."),
                ],
                attachTo: "li a[data-target-id='category-1'] right"
            }, {
                title: gettext("Products"),
                text: [
                    gettext("All your exciting products and features are located here.")
                ],
                attachTo: "li a[data-target-id='category-2'] right"
            }, {
                title: gettext("Contacts"),
                text: [
                    gettext("All your customer data is located here. Target and organize your clients details your way!")
                ],
                attachTo: "li a[data-target-id='category-3'] right"
            }
        ]);

        if($("li a[data-target-id='category-4']").length > 0) {
            steps.push({
                title: gettext("Reports"),
                text: [
                    gettext("Your reporting tool to build and analyze your consumer behavior information that can assist with your business decisions.")
                ],
                attachTo: "li a[data-target-id='category-4'] right"
            });
        }

        if($("li a[data-target-id='category-5']").length > 0) {
            steps.push({
                title: gettext("Campaigns"),
                text: [
                    gettext("Great loyalty tool for creating marketing, campaigns, special offers and coupons to entice your shoppers!"),
                    gettext("Set offers based on their previous purchase behavior to up- and cross sale your inventory.")
                ],
                attachTo: "li a[data-target-id='category-5'] right"
            });
        }

        steps.push({
            title: gettext("Storefront"),
            text: [
                gettext("The make-over tool to customize you site themes, add pages and product carousels. Incorporate any media to make your store pop!")
            ],
            attachTo: "li a[data-target-id='category-6'] right"
        });

        if($("li a[data-target-id='category-7']").length > 0){
            steps.push({
                title: gettext("Addons"),
                text: [
                    gettext("This is your connection interface. Addons and other systems you use can be attached to your store through powerful data connections."),
                    gettext("Supercharge your site and gather crazy amounts of data with integrations to CRMs and ERPs, POS’s and PIM’s, or any other acronym you can think of.")
                ],
                attachTo: "li a[data-target-id='category-7'] right"
            });
        }

        steps = steps.concat([{
            title: gettext("Settings"),
            text: [
                gettext("The nuts and bolts of your store are found here. From individual country tax-regulations to your contact details.")
            ],
            attachTo: "li a[data-target-id='category-8'] right"
        }, {
            title: gettext("Search"),
            text: [
                gettext("Lost and cannot find your way? No worries, you can search contacts, settings, add-ons and more features from here.")
            ],
            attachTo: "#site-search bottom"
        }, {
            title: gettext("View your storefront"),
            text: [
                gettext("Preview your shop and all the cool features you have created!")
            ],
            attachTo: ".shop-btn left"
        }, {
            title: gettext("We're done!"),
            text: [
                gettext("It was nice to show you around!"),
                gettext("If you need to run it again, fire it up from the menu in the top right.")
            ]
        }]);
        return steps;
    }

    $(document).ready(function() {
        $("#top-header .show-tour-li").on("click", "a", function(e){
            e.preventDefault();
            $.tour();
        });
    });

    $.tour = function(config={}, params) {
        if(config === "setPageSteps") {
            this.pageSteps = params;
            return;
        }
        let tour = new Shepherd.Tour({
            defaults: {
                classes: "shepherd-theme-arrows",
                scrollTo: true,
                showCancelLink: true
            }
        });

        var steps = [];
        if (this.pageSteps && this.pageSteps.length > 1) {
            steps = this.pageSteps;
        }
        else {
            steps = (this.pageSteps || []).concat(getAppChromeSteps(config.tourKey));
        }

        $.each(steps, (idx, step) => {
            var buttonType = null;
            if(idx === 0) {
                buttonType = "first";
            }
            if(idx === steps.length - 1) {
                buttonType = "last";
            }
            step = $.extend({}, step, {buttons: getTourButtons(buttonType)});
            let content = "";
            if(step.icon) {
                content += "<div class='clearfix'>";
                content += "<div class='pull-left'>";
                content += "<div class='icon'>";
                content += "<img src='" + step.icon + "' />";
                content += "</div>";
                content += "</div>";
                content += "<div class='step-with-icon'>";
                content += getTextLines(step.text);
                content += getHelpButton(step.helpPage);
                content += "</div>";
                content += "</div>";
            } else {
                content += getTextLines(step.text);
                content += getHelpButton(step.helpPage);
            }
            step.text = content;
            tour.addStep("step-" + idx, step);
        });

        function getTextLines(text) {
            let content = "";
            for(let i = 0; i < text.length; i++) {
                content += "<p class='lead'>" + text[i] + "</p>";
            }
            return content;
        }

        function getHelpButton(page) {
            let content = "";
            if(page) {
                let helpUrl = "http://shuup-guide.readthedocs.io/en/latest/" + page;
                content += "<br>";
                content += "<p class='text-center'>";
                content += "<a href='" + helpUrl + "' class='btn btn-inverse btn-default', target='_blank'>";
                content += "<i class='fa fa-info-circle'></i> " + gettext("Learn more at the Shuup Help Center");
                content += "</a>";
                content += "</p>";
            }
            return content;

        }
        function getTourButtons(type) {
            let buttons = [];
            if(type !== "first" && type !== "last") {
                buttons.push({
                    text: "Previous",
                    classes: "btn shepherd-button-secondary",
                    action: tour.back
                });
            }

            if(type == "last") {
                buttons.push({
                    text: "OK",
                    classes: "btn btn-primary",
                    action: tour.cancel
                });
            } else {
                buttons.push({
                    text: "Next",
                    classes: "btn btn-primary",
                    action: tour.next
                });
            }

            return buttons;
        }

        if(config.tourKey) {
            tour.on("cancel", () => {
                $.post("/sa/tour/", {"csrfmiddlewaretoken": window.ShuupAdminConfig.csrf, "tourKey": config.tourKey});
            });
        }
        tour.start();
        return tour;
    };
}(jQuery));
