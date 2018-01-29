/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
$(function() {
    $(".carousel-plugin.one").each(function () {
        var autoplay = JSON.parse($(this).data("autoplay"));
        var interval = JSON.parse($(this).data("interval"));
        var arrowsVisible = JSON.parse($(this).data("arrows-visible").toLowerCase());
        var pauseOnHover = JSON.parse($(this).data("pause-on-hover").toLowerCase());
        var useDotNavigation = JSON.parse($(this).data("use-dot-navigation").toLowerCase());
        $(this).owlCarousel({
            loop: true,
            autoplay: autoplay,
            autoplayTimeout: interval,
            autoplayHoverPause: pauseOnHover,
            nav: arrowsVisible,
            navText: [
                '<i class="fa fa-angle-left .carousel-control .icon-prev"></i>',
                '<i class="fa fa-angle-right .carousel-control .icon-prev"></i>'
            ],
            dots: useDotNavigation,
            items: 1
        });
    });

    slideCountToResponsiveData = {
        2: {0: {items: 1}, 640: {items: 2}, 992: {items: 2}},
        3: {0: {items: 2}, 640: {items: 2}, 992: {items: 3}},
    };

    $(".carousel-plugin.banner").each(function () {
        var slideCount = JSON.parse($(this).data("slide-count"));
        var arrowsVisible = JSON.parse($(this).data("arrows-visible").toLowerCase());
        var responsiveConfigure = slideCountToResponsiveData[slideCount];
        $(this).owlCarousel({
            margin: 30,
            nav: arrowsVisible,
            navText: [
                '<i class="fa fa-angle-left .carousel-control .icon-prev"></i>',
                '<i class="fa fa-angle-right .carousel-control .icon-prev"></i>'
            ],
            responsiveClass: true,
            responsive: (responsiveConfigure ? responsiveConfigure : {0: {items: 2}, 640: {items: 2}, 992: {items: 4}})
        });
    });
});
