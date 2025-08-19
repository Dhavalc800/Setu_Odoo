/** @odoo-module **/
import {useService} from "@web/core/utils/hooks";
import {OS_Dropdown} from "@os_theme_butterfly/components/os_dropdown/os_dropdown";

const {Component, onWillStart} = owl;

export class OsRecentlyViewedMenu extends Component {
    setup() {
        super.setup();
        onWillStart(async () => {
            this.records = await this.loadRecords("/theme/get/recently/viewed/records");
        });
        this.rpc = useService("rpc");
        this.env.bus.on('RECENTLY_ACTION_PERFORMED', this, this.update);
    }


    async loadRecords(Route) {
        return await this.rpc(Route);
    }

    async update(data) {
        this.records = data;
        this.render();
    }

    _onClickRecord(ev) {
        let res_model = $(ev.currentTarget).data("res_model");
        let res_id = $(ev.currentTarget).data("res_id");
        let name = $(ev.currentTarget).data("name");

        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: name,
            res_model: res_model,
            res_id: res_id,
            views: [[false, 'form']],
            target: 'current'
        });
    }

}

OsRecentlyViewedMenu.template = "os_theme_butterfly.os_recently_viewed_menu";
OsRecentlyViewedMenu.components = {
    OS_Dropdown,
};