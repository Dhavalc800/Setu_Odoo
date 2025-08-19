/** @odoo-module **/
import {patch} from "@web/core/utils/patch";
import {FormController} from "@web/views/form/form_controller";
import {useService} from "@web/core/utils/hooks";

patch(FormController.prototype, "os_theme_butterfly.recently_viewed_record", {
    setup() {
        this._super();
        var self = this;
        this.rpc = useService("rpc");
        this.action = useService('action');
        let action = false;

        const currentController = this.action.currentController;
        if (currentController && currentController.action.id) {
            action = currentController && currentController.action.id;
        } else {
            action = this.props.context.params?.action
        }

        if (this.props.resId  && this.props.resModel && action) {
            var data = {
                'res_id': this.props.resId,
                'model': this.props.resModel,
                'action': action,
            }
            this.rpc("/theme/recently/viewed/records", {data: data}).then(function (data) {
                self.env.bus.trigger('RECENTLY_ACTION_PERFORMED', data);
            });

        }
    },
});