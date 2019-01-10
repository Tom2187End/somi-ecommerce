/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    $(".form-control.datetime").datetimepicker({
        format: "Y-m-d H:i"
    });

    $(".form-control.date").datetimepicker({
        format: "Y-m-d",
        timepicker: false
    });

    $(".form-control.time").datetimepicker({
        format: "H:i",
        datepicker: false
    });
});

