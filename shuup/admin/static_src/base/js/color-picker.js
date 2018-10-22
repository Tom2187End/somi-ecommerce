/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */

function activateColorPicker(el) {
    $(el).colorpicker({
        format: "hex",
        horizontal: true
    });
}
window.activateColorPicker = activateColorPicker;

$(function() {
    $(".hex-color-picker").each((index, el) => {
        activateColorPicker(el);
    });
});
