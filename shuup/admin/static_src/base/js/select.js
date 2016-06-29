/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */

function activateSelects() {
    $("select").each(function(idx, object) {
        const select = $(object);
        const model = select.data("model");
        if(model === undefined) {
            select.select2({language: "xx"});
            return true;
        }
        select.select2({
            language: "xx",
            minimumInputLength: 3,
            ajax: {
                url: "/sa/select",
                dataType: "json",
                data: function(params) {
                    return {model: model, search: params.term};
                },
                processResults: function (data) {
                    return {
                        results: $.map(data.results, function (item) {
                            return {text: item.name, id: item.id};
                        })
                    };
                }
            }
        });
    });
}

$(function(){
    // Handle localization with Django instead of using select2 localization files
    $.fn.select2.amd.define("select2/i18n/xx", [], function () {
        return {
            errorLoading: function () {
                return gettext("The results could not be loaded");
            },
            inputTooLong: function (args) {
                var overChars = args.input.length - args.maximum;
                var message = ngettext(
                    "Please delete %s character",
                    "Please delete %s characters", overChars
                );
                return interpolate(message, [overChars]);
            },
            inputTooShort: function (args) {
                var remainingChars = args.minimum - args.input.length;
                return interpolate(gettext("Please enter %s or more characters"), [remainingChars]);
            },
            loadingMore: function () {
                return gettext("Loading more results...");
            },
            maximumSelected: function (args) {
                var message = ngettext(
                    "You can only select %s item",
                    "You can only select %s items", args.maximum
                );
                return interpolate(message, [args.maximum]);
            },
            noResults: function () {
                return gettext("No results found");
            },
            searching: function () {
                return gettext("Searching...");
            }
        };
    });
    activateSelects();
});
