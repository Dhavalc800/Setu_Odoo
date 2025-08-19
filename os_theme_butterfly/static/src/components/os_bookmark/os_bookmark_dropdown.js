/** @odoo-module */

import {OS_Dropdown} from "@os_theme_butterfly/components/os_dropdown/os_dropdown";
import {Dropdown} from "@web/core/dropdown/dropdown";
export class OsBookmarkDropdown extends Dropdown {
    setup() {
        super.setup(...arguments);
    }

    onDropdownStateChanged(args) {
        if (!this.rootRef.el || this.rootRef.el.contains(args.emitter.rootRef.el)) {
            this.env.bus.trigger('BOOKMARK:CLOSE_DROPDOWN');
        }
        return super.onDropdownStateChanged(...arguments);
    }

    close() {
        this.env.bus.trigger('BOOKMARK:CLOSE_DROPDOWN');
        return super.close(...arguments);
    }
}

OsBookmarkDropdown.template = OS_Dropdown.template;
