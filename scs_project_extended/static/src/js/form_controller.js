/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import session from 'web.session';

patch(FormController.prototype, "FormController.readonly", {
    async setup() {
        if (this.props.resModel && this.props.resModel == "res.partner"){
            this.props.preventEdit = session?.prevent_edit
        }
        return this._super.apply(this, arguments);
    },
});