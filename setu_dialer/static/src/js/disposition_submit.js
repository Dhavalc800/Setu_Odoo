/** @odoo-module **/

import { registry } from '@web/core/registry';
import { standardFieldProps } from '@web/views/fields/standard_field_props';
import { Component } from '@odoo/owl';

class SubmitDispositionButton extends Component {
    setup() {}
    
    async onClickSubmitDisposition() {
        console.log("\n\n\nConsoleeeeeeeeeeee")
        const record = this.props.record;
        const lead_id = record.data.lead_id && record.data.lead_id.res_id;
        const disposition_id = record.data.disposition_id && record.data.disposition_id.res_id;
        const fetch_lead_id = record.resId;
        const opportunity_name = record.data.opportunity_name || "";
        const expected_revenue = record.data.expected_revenue || 0.0;
        const remark = record.data.remark || "";

        if (!lead_id || !disposition_id || !fetch_lead_id) {
            alert("Missing required fields");
            return;
        }

        const payload = {
            lead_id,
            disposition_id,
            fetch_lead_id,
            opportunity_name,
            expected_revenue,
            remark,
        };

        try {
            const response = await this.env.services.rpc('/api/submit_disposition', payload);

            if (response.success) {
                await this.env.services.action.doAction({
                    type: 'ir.actions.act_window',
                    res_model: 'fetch.lead.user',
                    res_id: response.next_fetch_lead_id || fetch_lead_id,
                    view_mode: 'form',
                    target: 'current',
                });
            } else {
                alert("Error: " + (response.message || "Unknown error"));
            }
        } catch (error) {
            console.error("RPC error:", error);
            alert("Session expired or network error.");
        }
    }
}

SubmitDispositionButton.template = "setu_dialer.SubmitDispositionButton";
SubmitDispositionButton.props = {
    ...standardFieldProps,
};

registry.category("view_widgets").add("submit_disposition_button", SubmitDispositionButton);


// /** @odoo-module **/

// import { registry } from '@web/core/registry';
// import { standardFieldProps } from '@web/views/fields/standard_field_props';
// import { Component } from '@odoo/owl';

// const actionService = registry.category("services").get("action");

// class SubmitDispositionButton extends Component {
//     setup() {
//         super.setup();
//     }
//     debugger
//     async onClickSubmitDisposition() {
//         const record = this.props.record;
//         const lead_id = record.data.lead_id && record.data.lead_id.res_id;
//         const disposition_id = record.data.disposition_id && record.data.disposition_id.res_id;
//         const fetch_lead_id = record.resId;
//         const opportunity_name = record.data.opportunity_name || "";
//         const expected_revenue = record.data.expected_revenue || 0.0;
//         const remark = record.data.remark || "";

//         if (!lead_id || !disposition_id || !fetch_lead_id) {
//             alert("Missing required fields");
//             return;
//         }

//         const payload = {
//             lead_id,
//             disposition_id,
//             fetch_lead_id,
//             opportunity_name,
//             expected_revenue,
//             remark,
//         };

//         const response = await this.rpc("/api/submit_disposition", {
//             method: "POST",
//             data: JSON.stringify(payload),
//         });

//         if (response.success) {
//             this.env.services.action.doAction({
//                 type: 'ir.actions.act_window',
//                 res_model: 'fetch.lead.user',
//                 res_id: response.next_fetch_lead_id || fetch_lead_id,
//                 view_mode: 'form',
//                 target: 'current',
//             });
//         } else {
//             alert("Error: " + (response.message || "Unknown error"));
//         }
//     }
// }

// SubmitDispositionButton.template = "my_module.SubmitDispositionButton";
// SubmitDispositionButton.props = {
//     ...standardFieldProps,
// };

// registry.category("view_widgets").add("submit_disposition_button", SubmitDispositionButton);
