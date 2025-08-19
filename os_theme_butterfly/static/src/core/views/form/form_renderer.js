/** @odoo-module **/

import {FormRenderer} from "@web/views/form/form_renderer";

import {patch} from "@web/core/utils/patch";

patch(FormRenderer.prototype, 'OsFormRenderer', {

    setup() {
        this._super();
    },
    _onDblClick: function (ev) {
        var $target = $(ev.target);
        if ($target.parents('.modal').length || $target.parents('.o_Chatter').length || $target.is('.o_Chatter')) {
            return;
        }
        this.env.bus.trigger('FORM-VIEW:DblClickEdit');
    },
});
