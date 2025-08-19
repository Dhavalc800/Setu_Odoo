/** @odoo-module */

import {patch} from "@web/core/utils/patch";
import {SettingsPage} from "@web/webclient/settings_form_view/settings/settings_page";
import {session} from "@web/session";

patch(SettingsPage.prototype, "os_theme_butterfly.SettingsPage", {
    setup() {
        this._super();
    },
    getIconType() {
        return session.company_os_apps_icon_style;
    },
    getIconUrl: function (module) {
        return session.theme_settings_icons[module] ? session.theme_settings_icons[module] : session.theme_settings_icons["default"];
    },


});
