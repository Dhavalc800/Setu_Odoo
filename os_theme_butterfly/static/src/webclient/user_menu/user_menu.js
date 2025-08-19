/** @odoo-module */


import {patch} from "@web/core/utils/patch";
import {OS_Dropdown} from "@os_theme_butterfly/components/os_dropdown/os_dropdown";
import {OS_DropdownItem} from "@os_theme_butterfly/components/os_dropdown/os_dropdown_item";
import {UserMenu} from "@web/webclient/user_menu/user_menu";

patch(UserMenu, "os_theme_butterfly.UserMenu", {

    components: {
        ...UserMenu.components,
        OS_Dropdown,
        OS_DropdownItem,

    },
});