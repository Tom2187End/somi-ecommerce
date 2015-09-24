function showPreview(productId) {
    var modal_select = "#product-" + productId + "-modal";
    var product_modal = $(modal_select);
    if (product_modal.length) {
        product_modal.modal("show");
        return;
    }

    $.ajax({
        url: "/xtheme/product_preview",
        method: "GET",
        data: {
            id: productId
        },
        success: function(data) {
            $("body").append(data);
            $(modal_select).modal("show");
        }
    });
}

function setProductListViewMode(isInListMode) {
    if (typeof(Storage) !== "undefined") {
        localStorage.setItem("product_list_view_list_mode", (isInListMode ? "list" : "grid"));
    }
}

function getProductListViewMode() {
    if (typeof(Storage) !== "undefined") {
        return localStorage.getItem("product_list_view_list_mode");
    }
    return "grid";
}

function moveToPage(pageNumber) {
    var pagination = $("ul.pagination");
    // Prevent double clicking when ajax is loading
    if (pagination.prop("disabled")) {
        return false;
    }
    pagination.prop("disabled", true);

    if (typeof(pageNumber) !== "number") {
        pageNumber = parseInt(pageNumber);
        if (isNaN(pageNumber)) {
            return;
        }
    }
    window.PAGE_NUMBER = pageNumber;

    reloadProducts();
}

function reloadProducts() {
    var filterString = "?sort=" + $("#id_sort").val() + "&page=" + window.PAGE_NUMBER;
    $("#ajax_content").load(location.pathname + filterString);
}

function updateProductPrice(productId) {
    var $quantity = $("#product-quantity");
    if (!$quantity.is(":valid")) {
        return;
    }
    var data = {
        id: productId,
        quantity: $quantity.val()
    };
    var $selectedChild = $("#product-variations");
    if ($selectedChild.length > 0) {
        data.child = $selectedChild.val();
    }
    $.ajax({
        url: "/xtheme/product_price",
        method: "GET",
        data: data,
        success: function(html) {
            $("#product-price-section").html(html);
        }
    });
}

$(function() {
    $("#search-modal").on("show.bs.modal", function() {
        setTimeout(function(){
            $("#site-search").focus();
        }, 300)
    });

    function openMobileNav() {
        $(document.body).addClass("menu-open");
    }

    function closeMobileNav() {
        $(document.body).removeClass("menu-open");
    }

    function MobileNavIsOpen() {
        return $(document.body).hasClass("menu-open");
    }

    $(".toggle-mobile-nav").click(function(e) {
        e.stopPropagation();
        if (MobileNavIsOpen()) {
            closeMobileNav();
        } else {
            openMobileNav();
        }
    });

    $(document).click(function(e) {
        if (MobileNavIsOpen() && !$(e.target).closest(".pages .nav-collapse").length) {
            closeMobileNav();
        }

    });

    $(".main-nav .dropdown-menu").click(function(e) {
        e.stopPropagation();
    });

    $("#product-list-view-type").on("change", function() {
        var $productListView = $(".product-list-view");
        $productListView.toggleClass("list");
        setProductListViewMode($productListView.hasClass("list"));
    })

    $(".selectpicker").selectpicker();

    // By default product list view is in grid mode
    var $productListView = $(".product-list-view");
    if ($productListView.length > 0 && getProductListViewMode() == "list") {
        $productListView.addClass("list");
        $("#product-list-view-type").prop('checked', true);
    }

    // Add proper classes to category navigation based on current-page class
    var $currentlySelectedPage = $(".current-page");
    if ($currentlySelectedPage.length > 0) {
        $currentlySelectedPage.addClass("current");
        $currentlySelectedPage.parents("li").addClass("current");
    }
});
