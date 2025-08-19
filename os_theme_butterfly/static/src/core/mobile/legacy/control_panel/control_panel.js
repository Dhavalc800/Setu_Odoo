odoo.define('os_theme_butterfly.LegacyControlPanelMobile', function (require) {
    "use strict";
    const {device} = require('web.config');

    if (!device.isMobile) {
        return;
    }

    const ControlPanel = require('web.ControlPanel');
    const {patch} = require('web.utils');
    const {usePosition} = require("@web/core/position_hook");

    const {onMounted, useExternalListener, useRef, useState, useEffect} = owl;
    const CLASS = 'os_sticky_cp';


    patch(ControlPanel.prototype, 'os_theme_butterfly.LegacyControlPanelMobile', {
        setup() {
            this._super();

            this.controlPanelRef = useRef("controlPanel");

            this.state = useState({
                showSearchBar: false,
                showMobileSearch: false,
                showViewSwitcher: false,
            });

            this.onWindowClick = this._onWindowClick.bind(this);
            this.onScroll = this._onScrollThrottled.bind(this);

            useExternalListener(window, "click", this.onWindowClick);
            useEffect(() => {
                const element = this._getElement();
                element.addEventListener("scroll", this.onScroll);
                this.controlPanelRef.el.style.top = "0px";
                return () => {
                    element.removeEventListener("scroll", this.onScroll);
                }
            })
            onMounted(() => {
                this.old = 0;
                this.last = 0;
                this.initial = this._getElement().scrollTop;
            });
            if (this.props.views && this.props.views.length > 1) {
                const togglerRef = useRef("togglerRef");
                usePosition(() => togglerRef.el, {
                    popper: "menuRef",
                    position: "bottom-end",
                });
            }
        },

        _getElement() {
            return this.controlPanelRef.el.parentElement;
        },


        _resetSearchState() {
            Object.assign(this.state, {
                showSearchBar: false,
                showMobileSearch: false,
                showViewSwitcher: false,
            });
        },

        _onScrollThrottled() {
            if (!this.controlPanelRef.el || this.isScrolling) {
                return;
            }
            this.isScrolling = true;
            requestAnimationFrame(() => this.isScrolling = false);

            const scrollTop = this._getElement().scrollTop;
            const delta = Math.round(scrollTop - this.old);

            if (scrollTop > this.initial) {
                // Beneath initial position => sticky display
                this.controlPanelRef.el.classList.add(CLASS);
                this.last = delta < 0 ?
                    // Going up
                    Math.min(0, this.last - delta) :
                    // Going down | not moving
                    Math.max(-this.controlPanelRef.el.offsetHeight, -this.controlPanelRef.el.offsetTop - delta);
                this.controlPanelRef.el.style.top = `${this.last}px`;
            } else {
                // Above initial position => standard display
                this.controlPanelRef.el.classList.remove(CLASS);
                this.last = 0;
            }
            this.old = scrollTop;
        },


        _onSwitchView() {
            this._resetSearchState();
        },


        _onWindowClick(ev) {
            if (
                this.state.showViewSwitcher &&
                !ev.target.closest('.o_cp_switch_buttons')
            ) {
                this.state.showViewSwitcher = false;
            }
        },
    });

    patch(ControlPanel, 'os_theme_butterfly.LegacyControlPanelMobile', {
        template: 'os_theme_butterfly.LegacyControlPanelMobile',
    });
});
