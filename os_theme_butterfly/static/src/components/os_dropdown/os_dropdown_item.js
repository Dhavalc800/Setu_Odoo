/** @odoo-module */
import {DropdownItem} from "@web/core/dropdown/dropdown_item";

export class OS_DropdownItem extends DropdownItem {
    setup() {
        super.setup(...arguments);
    }
}

OS_DropdownItem.template = "os_theme_butterfly.OS_DropdownItem";
