/** @odoo-module */

import {OS_Dropdown} from "@os_theme_butterfly/components/os_dropdown/os_dropdown";
import {Dropdown} from "@web/core/dropdown/dropdown";

export class OS_Favorite_Apps_Dropdown extends Dropdown {
    setup() {
        document.addEventListener('click', (ev) => {
            if (this.rootRef.el.contains(ev.target) || $(document.activeElement).is('.os-favorite-app-dropdown .select2-input')) {
                return;
            } else {
                this.onWindowClickDropdown();
            }
        });
        super.setup(...arguments);

    }

    onWindowClickDropdown() {
        if (this.state.open) {
            this.close();
        }
    }

    onWindowClicked(ev) {
        if ($(document.activeElement).is('.os-favorite-app-dropdown  .select2-input')) {
            this.state.open = true;
        }
    }

    onDropdownStateChanged(args) {
        if (!this.rootRef.el || this.rootRef.el.contains(args.emitter.rootRef.el)) {
            this.env.bus.trigger('FAVORITE_APP:CLOSE_DROPDOWN');
        }
        return super.onDropdownStateChanged(...arguments);
    }

    close() {
        this.env.bus.trigger('FAVORITE_APP:CLOSE_DROPDOWN');
        return super.close(...arguments);
    }
}

OS_Favorite_Apps_Dropdown.template = OS_Dropdown.template;

