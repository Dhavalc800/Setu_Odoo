/** @odoo-module **/

import {FormCompiler} from "@web/views/form/form_compiler";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";


patch(FormCompiler.prototype, 'OsFormCompiler', {
    compile(node, params) {
        const compiled = this._super(node, params);
        compiled.children[0].classList.add('os_form_view');
        if (session.user_dbl_click_edit) {
            compiled.children[0].setAttribute("t-on-dblclick", "ev => this._onDblClick(ev)");
        }

        return compiled;
    },

});

