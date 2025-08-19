/** @odoo-module */

import {patch} from "@web/core/utils/patch";
import {OS_Dropdown} from "@os_theme_butterfly/components/os_dropdown/os_dropdown";
import { DebugMenu } from "@web/core/debug/debug_menu";

patch(DebugMenu, "os_theme_butterfly.SwitchCompanyMenu", {
    components: {
        ...DebugMenu.components,
        OS_Dropdown,
    },
});