/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
window.updatePrice = function updatePrice(productId) {
    var $quantity = $("#product-quantity-" + productId);
    if ($quantity.length === 0 || !$quantity.is(":valid")) {
        return;
    }

    var data = {
        // In case productId is not available try to fallback to first input with correct name
        id: productId ? productId : $("input[name=product_id]").val(),
        quantity: $quantity.val(),
        unitType: $("#product-unit-type-" + productId).val()
    };

    var $simpleVariationSelect = $("#product-variations-" + productId);
    if ($simpleVariationSelect.length > 0) {
        // Smells like a simple variation; use the selected child's ID instead.
        data.id = $simpleVariationSelect.val();
    } else {
        // See if we have variable variation select boxes; if we do, add those.
        $("select.variable-variation-" + productId).serializeArray().forEach(function(obj) {
            data[obj.name] = obj.value;
        });
    }
    jQuery.ajax({url: "/xtheme/product_price", dataType: "html", data: data}).done(function(responseText) {
        const $content = $("<div>").append($.parseHTML(responseText));
        const priceDiv = "#product-price-div-" + productId;

        if ($content.find("[id^='no-price']").length > 0) {
            $("#add-to-cart-button-" + productId).prop("disabled", true);
        } else {
            $("#add-to-cart-button-" + productId).not(".not-orderable").prop("disabled", false);
        }
        $(priceDiv).replaceWith($content.find(priceDiv));
    });
};
