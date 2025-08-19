/** @odoo-module */

import {patch} from "@web/core/utils/patch";
import {Notebook} from "@web/core/notebook/notebook";
import {session} from "@web/session";

const {device} = require('web.config');
const {useRef, onRendered, useExternalListener} = owl;

patch(Notebook.prototype, "os_theme_butterfly.Notebook", {
    setup() {
        this._super();
        var self = this;
        this.rootRef = useRef("notebookRef");
        this.alignement = session.company_tabs_alignment || 'horizontal';
        this.isMobile = device.isMobile;
        // this.scrollBarWidths = 40;
        /*onRendered(() => {
            setTimeout(function () {
                self.reAdjust();
            }, 500);
        });*/
        // useExternalListener(window, "resize", this.reAdjust);

    },

    widthOfList() {
        var itemsWidth = 0;
        $(this.rootRef.el).find('.notebook-list li').each(function () {
            var itemWidth = $(this).outerWidth();
            itemsWidth += itemWidth;
        });
        return itemsWidth;
    },

    getLeftPosi() {
        let $notebook_list = $(this.rootRef.el).find('.notebook-list');
        if ($notebook_list) {
            return $(this.rootRef.el).find('.notebook-list').position().left;

        } else {
            return 0
        }
    },

    widthOfHidden() {
        var $headers = $(this.rootRef.el).find('.o_notebook_headers');
        return (($headers.outerWidth()) - this.widthOfList() - this.getLeftPosi()) - this.scrollBarWidths;
    },

    reAdjust() {
        var $headers = $(this.rootRef.el).find('.o_notebook_headers');

        if (($headers.outerWidth()) < this.widthOfList()) {
            $(this.rootRef.el).find('.scroller-right').show(300);
        } else {
            $(this.rootRef.el).find('.scroller-right').hide(300);
        }

        if (this.getLeftPosi() < 0) {
            $(this.rootRef.el).find('.scroller-left').show(300);
        } else {
            $(this.rootRef.el).find('.notebook-list').animate({left: "-=" + this.getLeftPosi() + "px"}, 'slow');
            $(this.rootRef.el).find('.scroller-left').hide(300);
        }
    },

    onClickScrollRight() {
        $(this.rootRef.el).find('.scroller-left').fadeIn('slow');
        $(this.rootRef.el).find('.scroller-right').fadeOut('slow');
        $(this.rootRef.el).find('.notebook-list').animate({left: "+=" + this.widthOfHidden() + "px"}, 'slow', function () {
        });
    },

    onClickScrollLeft() {
        $(this.rootRef.el).find('.scroller-right').fadeIn('slow');
        $(this.rootRef.el).find('.scroller-left').fadeOut('slow');
        $(this.rootRef.el).find('.notebook-list').animate({left: "-=" + this.getLeftPosi() + "px"}, 'slow', function () {
        });
    }
});

