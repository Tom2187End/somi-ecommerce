/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    "use strict";
    $("[data-toggle=\"tooltip\"]").tooltip({
        delay: {"show": 750, "hide": 100}
    });
    $("#dropdownMenu").tooltip({
        delay: {"show": 750, "hide": 100}
    });
}());
