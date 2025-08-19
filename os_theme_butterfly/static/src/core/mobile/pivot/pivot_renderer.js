/** @odoo-module **/

import config from "web.config";

if (!config.device.isMobile) {
    return;
}
import {PivotRenderer} from "@web/views/pivot/pivot_renderer";
import {useEffect, useRef} from "@odoo/owl";
import {patch} from "web.utils";

patch(PivotRenderer.prototype, "pivot_mobile", {
    setup() {
        this._super();
        this.rootRef = useRef("root");
        useEffect(() => {
            const tooltipElems = this.rootRef.el.querySelectorAll("*[data-tooltip]");
            for (const el of tooltipElems) {
                el.removeAttribute("data-tooltip");
                el.removeAttribute("data-tooltip-position");
            }
        });

    },

    _getPadding(cell) {
        return 5 + cell.indent * 5;
    },
});


