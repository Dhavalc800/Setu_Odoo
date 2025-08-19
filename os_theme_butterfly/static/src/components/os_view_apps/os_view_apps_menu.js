/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";

const {Component, useRef, onMounted, onPatched} = owl;

export class OsViewAppsMenu extends Component {
    setup() {
        super.setup();
        this.osMenuAppsRefIcon = useRef("osMenuAppsIcon");
        this.osMenuAppsIconLi = useRef("osMenuAppsIconLi");
        this.viewApps = useService("view_apps");
        this.titleService = useService("title");
        this.env.bus.on("APPS-MENU-TOGGLED", this, () => this._toggleMenuIcon());
        onMounted(() => {
            this._toggleMenuIcon();
        });
        onPatched(() => {
            this._toggleMenuIcon();
        });
    }


    hasActionRunning() {
        return this.viewApps.hasAction;
    }

    isAppViewDisplayed() {
        return this.viewApps.is_displayed;
    }

    onClickToggleView() {
        var self = this;
        this.viewApps.toggleView().then(function () {
        });

    }

    _toggleMenuIcon() {
        var self = this;
        const element = this.osMenuAppsRefIcon.el;
        const elementParent = this.osMenuAppsIconLi.el;
        elementParent.classList.toggle("d-none", this.isAppViewDisplayed() && !this.hasActionRunning());
        element.classList.toggle("osi-grid", !this.isAppViewDisplayed());
        element.classList.toggle("osi-arrow-left-c", this.isAppViewDisplayed() && this.hasActionRunning());
    }
}

OsViewAppsMenu.template = "os_theme_butterfly.os_view_apps_menu";
