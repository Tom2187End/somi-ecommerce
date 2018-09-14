/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    $(".form-control.datetime").datepicker({
        format: "yyyy-mm-dd",
        autoHide: true
    });
    $(".form-control.date").datepicker({
        format: "yyyy-mm-dd",
        autoHide: true
    });
});
