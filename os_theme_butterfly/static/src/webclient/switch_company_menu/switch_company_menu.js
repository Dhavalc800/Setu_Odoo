/** @odoo-module */

import {patch} from "@web/core/utils/patch";
import {OS_Dropdown} from "@os_theme_butterfly/components/os_dropdown/os_dropdown";
import { SwitchCompanyMenu } from "@web/webclient/switch_company_menu/switch_company_menu";

patch(SwitchCompanyMenu, "os_theme_butterfly.SwitchCompanyMenu", {
    components: {
        ...SwitchCompanyMenu.components,
        OS_Dropdown,
    },
});