from odoo import http
from odoo.http import request
from datetime import datetime
import json

class PysicalMeetingController(http.Controller):

    @http.route('/pysical/meeting', type='http', auth='public', methods=['POST'], csrf=False)
    def create_pysical_meeting(self, **post):
        try:
            data = json.loads(request.httprequest.data)
        except Exception as e:
            return request.make_response(
                json.dumps({"status": "error", "message": f"Invalid JSON: {str(e)}"}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

        required_fields = ['email', 'contact']
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            return request.make_response(
                json.dumps({"status": "error", "message": f"Missing required fields: {', '.join(missing)}"}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

        # Check for duplicate contact
        existing = request.env['pysical.meeting'].sudo().search([('contact', '=', data.get('contact'))], limit=1)
        if existing:
            return request.make_response(
                json.dumps({"status": "error", "message": "Contact already exists."}),
                headers=[('Content-Type', 'application/json')],
                status=409
            )

        # Get employee's user_id from employee_code
        user_id = False
        employee_code = data.get('employee_code')
        if employee_code:
            employee = request.env['hr.employee'].sudo().search([('identification_no', '=', employee_code)], limit=1)
            if employee and employee.user_id:
                user_id = employee.user_id.id

        try:
            record = request.env['pysical.meeting'].sudo().create({
                'name': data.get('name', ''),
                'email': data.get('email'),
                'contact': data.get('contact'),
                'slab': data.get('slab', ''),
                'state': data.get('state', ''),
                'pincode': data.get('pincode', ''),
                'type': data.get('type', ''),
                'district': data.get('district', ''),
                'user_id': user_id,
                'disposition': data.get('disposition', ''),
            })
            return request.make_response(
                json.dumps({"status": "success", "message": "Record created", "id": record.id}),
                headers=[('Content-Type', 'application/json')],
                status=200
            )
        except Exception as e:
            return request.make_response(
                json.dumps({"status": "error", "message": str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )
    
    @http.route('/pysical/meeting/today', type='json', auth='public', methods=['POST'], csrf=False)
    def get_today_pysical_meetings(self):
        today = datetime.now().strftime('%Y-%m-%d')
        start_time = today + ' 00:00:00'
        end_time = today + ' 23:59:59'

        records = request.env['pysical.meeting'].sudo().search([
            ('meeting_date', '>=', start_time),
            ('meeting_date', '<=', end_time),
            ('stage_by_admin', '=', 'approve'),
        ])

        data = []
        for rec in records:
            data.append({
                'call_by_identification': rec.user_id.employee_id.identification_no if rec.user_id and rec.user_id.employee_id else '',
                'lead_id': rec.id,
                'lead_name': rec.name,
                'lead_details': {
                    'email': rec.email,
                    'phone': rec.contact,
                    'slab': rec.slab,
                    'state': rec.state,
                    'pincode': rec.pincode,
                    'type': rec.type,
                    'city': rec.state,
                    'district': rec.district,
                    'meeting_date': rec.meeting_date,
                    'user_id': rec.user_id.id if rec.user_id else '',
                    'user_name': rec.user_id.name if rec.user_id else '',
                    'create_date': rec.create_date.strftime('%Y-%m-%d %H:%M:%S') if rec.create_date else ''
                },
                'lead_disposition': rec.disposition or '',
                'call_by_id': rec.user_id.id if rec.user_id else '',
                'call_by_name': rec.user_id.name if rec.user_id else '',
                'meeting_person_details': {
                    'meeting_person_identification': rec.meeting_user_id.employee_id.identification_no if rec.meeting_user_id else '',
                    'meeting_person_name': rec.meeting_user_id.name if rec.meeting_user_id else '',
                    'meeting_person_id': rec.meeting_user_id.id if rec.meeting_user_id else '',
                }
            })

        return {
            "status": "success",
            "data": data
        }