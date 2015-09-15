function showPreview(productId) {
    var modal_select = "#product-" + productId + "-modal";
    var product_modal = $(modal_select);
    if (product_modal.length) {
        product_modal.modal("show");
        return;
    }

    $.ajax({
        url: '/xtheme/product_quick_view?id=' + productId,
        method: "GET",
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
});
