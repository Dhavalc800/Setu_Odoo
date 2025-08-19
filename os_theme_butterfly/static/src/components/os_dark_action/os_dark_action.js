/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";
import {registry} from "@web/core/registry";
const {Component, useRef} = owl;

export class OsDarkAction extends Component {
    setup() {
        super.setup();
        this.userThemeService = useService("os_user_settings");
        this.osMenuDarkIconRef = useRef("osMenuDarkIcon");
        this.rpc = useService("rpc");

    }

    async onClickDarkAction() {
        var self = this;
        let data_user = {
            'os_theme_mode': $(this.osMenuDarkIconRef.el).data("update"),
        }
        return await this.rpc("/web/theme/user/change_theme_mode", {data: data_user}).then(function (res) {
            self.env.services.action.doAction("reload_context");
        });
    }

}

OsDarkAction.template = 'os_theme_butterfly.os_dark_action';
export const systrayItem = {
    Component: OsDarkAction,
};

registry.category("systray").add("OsDarkAction", systrayItem, {sequence: 98});