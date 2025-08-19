from odoo import http
from odoo.http import request
from datetime import datetime
import json
import logging

_logger = logging.getLogger(__name__)


class LeadCallHistoryController(http.Controller):

    def parse_lead_details(self, detail_string):
        details_dict = {}
        lines = detail_string.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                details_dict[key.strip()] = value.strip()
        return details_dict

    @http.route('/fisical/expo', type='json', auth='public', methods=['POST'], csrf=False)
    def get_today_lead_calls(self):
        today = datetime.now().strftime('%Y-%m-%d')
        start_time = today + ' 00:00:00'
        end_time = today + ' 23:59:59'

        records = request.env['lead.call.history'].sudo().search([
            ('disposition_id.is_expo', '=', True),
            ('create_date', '>=', start_time),
            ('create_date', '<=', end_time)
        ])

        data = []
        for rec in records:
            data.append({
                'call_by_identification': rec.user_id.employee_id.identification_no if rec.user_id and rec.user_id.employee_id else '',
                'lead_id': rec.lead_id.id,
                'lead_name': rec.lead_id.display_name,
                'lead_details': self.parse_lead_details(rec.lead_id.dynamic_field_values),
                'lead_disposition': rec.disposition_id.name if rec.disposition_id else '',
                'call_by_id': rec.user_id.id if rec.user_id else '',
                'call_by_name': rec.user_id.display_name if rec.user_id else '',
            })

        return {"status": "success", "data": data}

    @http.route('/lead/management/today', type='json', auth='public', methods=['POST'], csrf=False)
    def get_today_lead_management(self):
        today = datetime.now().strftime('%Y-%m-%d')
        start_time = today + ' 00:00:00'
        end_time = today + ' 23:59:59'

        records = request.env['lead.management'].sudo().search([
            ('dispostion_id.is_expo', '=', True),
            ('datetime', '>=', start_time),
            ('datetime', '<=', end_time)
        ])
        data = []
        for rec in records:
            data.append({
                'call_by_identification': rec.user_id.employee_id.identification_no if rec.user_id and rec.user_id.employee_id else '',
                'lead_id': rec.id,
                'lead_name': rec.name,
                'lead_details': {
                    'email': rec.email,
                    'phone': rec.phone,
                    'slab': rec.slab,
                    'service': rec.service,
                    'source': rec.source,
                    'type': rec.type,
                    'city': rec.city,
                    'lead_type': rec.lead_type,
                    'datetime': rec.datetime.strftime('%Y-%m-%d %H:%M:%S') if rec.datetime else '',
                    'remarks': rec.remarks,
                },
                'lead_disposition': rec.dispostion_id.name if rec.dispostion_id else '',
                'call_by_id': rec.user_id.id if rec.user_id else '',
                'call_by_name': rec.user_id.name if rec.user_id else '',
                'meeting_person_details': {
                    'meeting_person_identification': rec.meeting_user_id.employee_id.identification_no if rec.meeting_user_id else '',
                    'meeting_person_name': rec.meeting_user_id.name if rec.meeting_user_id else '',
                    'meeting_person_id': rec.meeting_user_id.id if rec.meeting_user_id else '',
                }
            })

        return {"status": "success", "data": data}
    
    @http.route('/lead/management/rescheduled/today', type='json', auth='public', methods=['POST'], csrf=False)
    def get_today_rescheduled_leads(self):
        today = datetime.now().strftime('%Y-%m-%d')
        start_time = today + ' 00:00:00'
        end_time = today + ' 23:59:59'

        # Search leads whose reschedule_date is today
        records = request.env['lead.management'].sudo().search([
            ('reschedule_date', '>=', start_time),
            ('reschedule_date', '<=', end_time)
        ])

        data = []
        for rec in records:
            data.append({
                'call_by_identification': rec.user_id.employee_id.identification_no if rec.user_id and rec.user_id.employee_id else '',
                'lead_id': rec.id,
                'lead_name': rec.name,
                'lead_details': {
                    'email': rec.email,
                    'phone': rec.phone,
                    'slab': rec.slab,
                    'service': rec.service,
                    'source': rec.source,
                    'type': rec.type,
                    'city': rec.city,
                    'lead_type': rec.lead_type,
                    'datetime': rec.datetime.strftime('%Y-%m-%d %H:%M:%S') if rec.datetime else '',
                    'reschedule_date': rec.reschedule_date.strftime('%Y-%m-%d %H:%M:%S') if rec.reschedule_date else '',
                    'remarks': rec.remarks,
                },
                'lead_disposition': rec.dispostion_id.name if rec.dispostion_id else '',
                'call_by_id': rec.user_id.id if rec.user_id else '',
                'call_by_name': rec.user_id.name if rec.user_id else '',
                'meeting_person_details': {
                    'meeting_person_identification': rec.meeting_user_id.employee_id.identification_no if rec.meeting_user_id else '',
                    'meeting_person_name': rec.meeting_user_id.name if rec.meeting_user_id else '',
                    'meeting_person_id': rec.meeting_user_id.id if rec.meeting_user_id else '',
                }
            })

        return {"status": "success", "data": data}

    # @http.route('/api/booking', type='json', auth='public', methods=['POST'], csrf=False)
    # def get_booking_data(self, **kwargs):
    #     # Get API key from headers
    #     api_key = request.httprequest.headers.get('Api-Key')
    #     headers = dict(request.httprequest.headers)
    #     _logger.info("\n\nHEADERS RECEIVED: %s", headers)
    #     print("\n\n\n\nApiiiiiiiiiiiiiiii",api_key)
    #     if api_key != 'qrt_booking_2025#':
    #         return {
    #             'error': 'Unauthorized',
    #             'message': 'Invalid API key'
    #         }

    #     # Load raw JSON data from the request
    #     try:
    #         data = json.loads(request.httprequest.data)
    #     except Exception:
    #         return {
    #             'error': 'Bad Request',
    #             'message': 'Invalid JSON format'
    #         }

    #     booking_id = data.get('booking_id')
    #     if not booking_id:
    #         return {
    #             'error': 'Bad Request',
    #             'message': 'Missing booking_id in request'
    #         }

    #     # Search for the sale order
    #     sale_order = request.env['sale.order'].sudo().search([
    #         ('name', '=', booking_id)
    #     ], limit=1)

    #     if not sale_order:
    #         return {
    #             'error': 'Not Found',
    #             'message': 'Booking not found'
    #         }

    #     # Return booking details
    #     return {
    #         'company_name': sale_order.partner_id.name or '',
    #         'amount': sale_order.amount_total,
    #         'email': sale_order.partner_id.email or '',
    #         'phone': sale_order.partner_id.mobile or '',
    #         'booking_status': sale_order.state
    #     }
