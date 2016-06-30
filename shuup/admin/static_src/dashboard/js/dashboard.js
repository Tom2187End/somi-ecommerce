/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* eslint-disable no-unused-vars */
$(function() {
    "use strict";
    if (window.DashboardCharts) {
        window.DashboardCharts.init();
    }
    if (window.Masonry) {
        const Masonry = window.Masonry;

        const msnry = new Masonry(document.getElementById("dashboard-wrapper"), {
            itemSelector: ".block",
            columnWidth: ".block"
        });
    }
    $(document).on("click", "button.dismiss-button", function() {
        const $button = $(this);
        const url = $button.data("dismissUrl");
        if (!url) {
            return;
        }
        $.ajax({
            type: "POST",
            url: url,
            dataType: "json",
            success: function(data) {
                if (data.ok) {
                    const dismissTarget = $button.data("dismissTarget");
                    if (dismissTarget) {
                        $(dismissTarget).remove();
                    }
                }
                if (data.error && window.Messages) {
                    window.Messages.enqueue({text: data.error});
                }
            }
        });
    });

});
