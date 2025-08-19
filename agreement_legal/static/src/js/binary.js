/** @odoo-module **/

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { BinaryField } from "@web/views/fields/binary/binary_field";
import { useService } from "@web/core/utils/hooks";

patch(BinaryField.prototype, "binary_preview", {
    setup(){
        this._super(...arguments)
        this.action = useService("action");
    },
    PreviewFile(){
        return  this.action.doAction({
            type: 'ir.actions.act_url',
            url: `/web/content/${this.props.record.resModel}/${this.props.record.resId}/${this.props.name}/${this.fileName}`,
        });
    }
});

