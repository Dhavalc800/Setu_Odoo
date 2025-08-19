/** @odoo-module **/

import {FormController} from '@web/views/form/form_controller';

import {patch} from "@web/core/utils/patch";

patch(FormController.prototype, 'OsFormController', {

    async setup() {
        this._super();
        this.env.bus.on("FORM-VIEW:DblClickEdit", this, async () => {
                if (this.model.root.mode === "edit") {
                    await this.model.root.switchMode("readonly");
                } else {
                    await this.model.root.switchMode("edit");
                }
            }
        );
    },

});
