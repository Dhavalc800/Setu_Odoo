/** @odoo-module **/

const {Component, useRef} = owl;
import {registry} from "@web/core/registry";

export class OsHeaderToolsBarMenu extends Component {
    setup() {
        this.rootRef = useRef("root");

    }

    toggleHeaderToolsBar() {
        $(".os-header-toolsbar").toggleClass('is-fixed');
        $(".os-content").toggleClass('os-header-toolsbar-shown');
        $("body").toggleClass('os-header-toolsbar-shown');
        $(this.rootRef.el).toggleClass("shown");
    }
}

OsHeaderToolsBarMenu.template = "os_theme_butterfly.OsHeaderToolsBarMenu";

export const systrayItem = {
    Component: OsHeaderToolsBarMenu,
};

registry.category("systray").add("OsHeaderToolsBarMenu", systrayItem, {sequence: -1});