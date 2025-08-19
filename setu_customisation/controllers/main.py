from odoo import http
from odoo.http import request
import json

class LeadController(http.Controller):
    
    @http.route('/api/lead', type='json', auth='public', methods=['POST'], csrf=False)
    def create_lead(self, **kwargs):
        # Static JSON data
        json_data = json.loads(request.httprequest.data)
        
        # Extract data from the JSON
        lead_name = json_data.get('lead_name')
        contact = json_data.get('contact')
        email = json_data.get('email')
        source = json_data.get('source')
        company_type = json_data.get('company_type')
        slab = json_data.get('slab')
        disposition = json_data.get('disposition')
        employee_code = json_data.get('employee_code')
        service = json_data.get('service')
        campaign_name = json_data.get('campaign_name')

        # Search for an existing partner
        partner = request.env['res.partner'].sudo().search([('name', '=', lead_name), ('phone', '=', contact)], limit=1)
        if not partner:
            # Create a new partner if none exists
            partner = request.env['res.partner'].sudo().create({
                'name': lead_name,
                'email': email,
                'phone': contact,
            })

        # Search for an existing employee based on employee_code
        employee = request.env['hr.employee'].sudo().search([('identification_no', '=', employee_code)], limit=1)
        if employee:
            added_by = employee.user_id.id if employee.user_id else False  # Safely get the user ID linked to the employee
        else:
            added_by = 2
        
        # Create a new lead record
        lead = request.env['lead.details'].sudo().create({
            # 'lead_name': lead_name,
            'phone_number': contact,
            'crm_phone': contact,
            'lead_email': email,
            'lead_source': source,
            'company_type': company_type,
            'lead_slab': slab,
            'lead_disposition': disposition,
            'assign_user_id': added_by,
            'lead_service': service,
            'campaign_name': campaign_name,
            'lead_partner_id': partner.id,
        })
        
        # Return a success response
        return {'status': 'success', 'lead_id': lead.id}

