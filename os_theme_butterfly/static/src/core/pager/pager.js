/** @odoo-module **/
import {Pager} from "@web/core/pager/pager";
import {ViewReloader} from "./reloader";

Pager.components = Object.assign({}, Pager.components, {
    ViewReloader,
});
