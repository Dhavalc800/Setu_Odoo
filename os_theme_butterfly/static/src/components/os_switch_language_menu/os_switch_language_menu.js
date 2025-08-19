/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";
import {registry} from "@web/core/registry";
import {session} from "@web/session";
import {OS_Dropdown} from "@os_theme_butterfly/components/os_dropdown/os_dropdown";

const {Component, onWillStart} = owl;

export class OsSwitchLanguageMenu extends Component {
    setup() {
        super.setup();
        onWillStart(async () => {
            this.languages = await this.loadLanguages("/get/installed/languages");
        });
        this.rpc = useService("rpc");
        this.user = useService("user");
        this.current_language = String(session.user_context.lang);

    }

    async loadLanguages(Route) {
        return await this.rpc(Route, {context: this.user.context});
    }

    toggleLanguageClick(ev) {
        var self = this;
        var selected_language = $(ev.currentTarget).data("language-code");
        self.rpc("get/selected/language", {
            selected_language: selected_language,
        }).then(function () {
            self.env.services.action.doAction("reload_context");

        });
    }

}

OsSwitchLanguageMenu.template = "os_theme_butterfly.os_switch_language";
OsSwitchLanguageMenu.components = {
    OS_Dropdown
}
OsSwitchLanguageMenu.toggleDelay = 1000;

export const systrayItem = {
    Component: OsSwitchLanguageMenu,
};

registry.category("systray").add("OsSwitchLanguageMenu", systrayItem, {sequence: 1});