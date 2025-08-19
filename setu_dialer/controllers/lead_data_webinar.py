from odoo import http
from odoo.http import request
import json

class LeadDataAPIController(http.Controller):

    @http.route('/api/create_lead_data', type='json', auth='public', methods=['POST'], csrf=False)
    def create_lead_data(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data)

            phone = data.get('phone', '').strip()
            phone_last10 = phone[-10:] if phone else False

            # 1) Check for duplicate on phone
            if phone_last10:
                dup = request.env['lead.data.lead'].sudo().search([
                    ('x_phone', 'ilike', phone_last10)
                ], limit=1)
                if dup:
                    return {
                        "success": False,
                        "message": "Duplicate lead. Phone already exists.",
                        "lead_id": dup.id
                    }

            # 2) Set standard + custom fields
            lead = request.env['lead.list.data'].sudo().search([('id', '=', data.get('lead_list_id'))], limit=1)
            lead_id = lead.id if lead else False
            campaign = lead.campaign_id.id if lead else False

            vals = {
                'x_name': data.get('name'),
                'x_email': data.get('email'),
                'x_phone': data.get('phone'),
                'x_company': data.get('company'),
                'x_slab': data.get('slab'),
                'x_source': data.get('source'),
                'x_service': data.get('service'),
                'x_rejected_date': data.get('rejected_date'),
                'x_apply_for': data.get('apply_for'),
                'x_representative_name': data.get('representative_name'),
                'x_state': data.get('state', '') if data.get('state') else False,
                'x_incomplete_description': data.get('incomplete_description'),
                'lead_list_id': lead_id,
                'campaign_id': campaign,
                # Uncomment these fields and modify them as needed
                # 'x_slab': data.get('slab'),
                # 'x_service': data.get('service'),
                # 'x_source': data.get('source'),
                # 'x_companysource': data.get('CompanySource'),
                'x_type': data.get('type'),
                'x_bm_name': data.get('bm_name'),
                'x_date': data.get('date'),
                'x_time': data.get('time'),
                # 'x_connected_bdm': data.get('Connected BDM'),
            }

            lead = request.env['lead.data.lead'].sudo().create(vals)

            return {
                "success": True,
                "message": "Lead data created successfully.",
                "lead_id": lead.id,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
