odoo.define('os_theme_butterfly.BasicModel', function (require) {
    "use strict";
    var BasicModel = require('web.BasicModel');
    const {browser} = require("@web/core/browser/browser");
    var session = require('web.session');
    const {parseHash} = require("@web/core/browser/router_service");
    var ajax = require('web.ajax');

    BasicModel.include({

        _load: function (dataPoint, options) {
            if (session.user_display_bookmarks) {
                browser.setTimeout(async function () {
                    const hash = browser.location.hash;
                    let current_url = parseHash(hash);
                    if (current_url.action) {
                        await ajax.rpc("/theme/get/bookmark", {}).then(function (data) {
                            let links = _.map(data, 'link');
                            let is_bookmarked = _.some(links, function (res) {
                                let url = parseHash(res);
                                return url.action === current_url.action;
                            });

                            if (is_bookmarked) {
                                $('#icon_bookmark').addClass("text-warning").removeClass('osi-bookmark').addClass('osi-bookmark-fill');
                            } else {
                                $('#icon_bookmark').removeClass("text-warning").removeClass('osi-bookmark-fill').addClass('osi-bookmark');
                            }
                        });
                    }


                }, 2000);

            }

            $("#scrollToTop").hide('500');
            browser.setTimeout(function () {
                $('.o_content').on("scroll", function () {
                    var topPos = $(this).scrollTop();
                    if (topPos > 100) {
                        $("#scrollToTop").show('500');

                    } else {
                        $("#scrollToTop").hide('500');
                    }

                });
            }, 2000);
            return this._super.apply(this, arguments);


        }
    });
});


