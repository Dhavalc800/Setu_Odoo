# controllers/lead_api.py
from odoo import http
from odoo.http import request
import json

class LeadAPIController(http.Controller):

    @http.route('/api/create_manual_lead', type='json', auth='public', methods=['POST'], csrf=False)
    def create_manual_lead(self, **kwargs):
        try:
            # 1) Load payload
            data = json.loads(request.httprequest.data)

            # 2) Dedup on phone
            phone = data.get('phone', '').strip()
            phone_last10 = phone[-10:] if phone else False
            if phone_last10:
                dup = request.env['lean.manual.lead'].sudo().search([
                    ('phone', 'ilike', phone_last10)
                ], limit=1)
                if dup:
                    return {
                        "success": False,
                        "message": "Duplicate lead. Phone already exists.",
                        "lead_id": dup.id
                    }

            # 3) Map standard fields
            emp_code     = data.get('EmployeeCode')
            company_name = data.get('companyname')
            email        = data.get('email')
            slab         = data.get('slab')
            bdm          = data.get('bdm') or ''
            source       = data.get('source')
            state        = data.get('state')
            service      = data.get('service')

            # 4) Resolve employee → user
            emp = request.env['hr.employee'].sudo().search([
                ('identification_no', '=', emp_code)
            ], limit=1)
            user_id = emp.user_id.id if emp and emp.user_id else request.env.uid

            # 5) Prepare vals dict
            vals = {
                'employee_id':  user_id,
                'company_name': company_name,
                'phone':        phone,
                'email':        email,
                'slab':         slab,
                'bdm':          bdm,
                'source':       source,
                'state':        state,
                'service':      service,
            }

            # 6) Dynamically add any extra keys
            #    (and collect a summary for dynamic_* fields)
            standard_keys = {
                'EmployeeCode', 'companyname', 'phone', 'email',
                'slab', 'bdm', 'source', 'state', 'service'
            }
            extra_lines = []
            # fetch the ir.model record for lean.manual.lead
            model = request.env['ir.model'].sudo().search([
                ('model', '=', 'lean.manual.lead')
            ], limit=1)

            for key, val in data.items():
                if key in standard_keys or val is None:
                    continue
                display = key
                field_name = 'x_' + display.lower().replace(' ', '_')
                # create the field if missing
                existing = request.env['ir.model.fields'].sudo().search([
                    ('model_id', '=', model.id),
                    ('name',     '=', field_name),
                ], limit=1)
                if not existing:
                    request.env['ir.model.fields'].sudo().create({
                        'model_id':          model.id,
                        'name':              field_name,
                        'field_description': display,
                        'ttype':             'char',
                        'state':             'manual',
                    })
                # add to vals + summary
                vals[field_name] = val
                extra_lines.append(f"{display}: {val}")

            # store extras in your text fields
            if extra_lines:
                summary = "\n".join(extra_lines)
                vals['dynamic_field_values'] = summary
                vals['dynamic_summary']      = summary

            # 7) Actually create
            lead = request.env['lean.manual.lead'].sudo().create(vals)

            return {
                "success": True,
                "message": "Lead created successfully",
                "lead_id": lead.id,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }




# from odoo import http
# from odoo.http import request
# import json

# class LeadAPIController(http.Controller):

#     @http.route('/api/create_manual_lead', type='json', auth='public', methods=['POST'], csrf=False)
#     def create_manual_lead(self, **kwargs):
#         try:
#             # Automatically parses JSON body into a dictionary
#             data = json.loads(request.httprequest.data)
#             emp_code = data.get('EmployeeCode')
#             company_name = data.get('companyname')
#             phone = data.get('phone')
#             email = data.get('email')
#             slab = data.get('slab')
#             bdm = data.get('bdm'),
#             source = data.get('source')
#             state = data.get('state')
#             service = data.get('service')

#             if isinstance(bdm, tuple):
#                 bdm = bdm[0]
            
#             # Check for duplicate phone number (last 10 digits)
#             if phone:
#                 phone_last10 = phone[-10:]
#                 existing_lead = request.env['lean.manual.lead'].sudo().search([
#                     ('phone', 'ilike', phone_last10)
#                 ], limit=1)
#                 if existing_lead:
#                     return {
#                         "success": False,
#                         "message": "Duplicate lead. Phone number already exists.",
#                         "lead_id": existing_lead.id
#                     }

#             # Search for employee by identification_no
#             employee = request.env['hr.employee'].sudo().search([
#                 ('identification_no', '=', emp_code)
#             ], limit=1)
#             if employee:
#                 user_id = employee.user_id.id if employee and employee.user_id else False
#             else:
#                 user_id = 2
#             if user_id:
#                 # Create the manual lead
#                 lead = request.env['lean.manual.lead'].sudo().create({
#                     'employee_id': user_id,                
#                     'company_name': company_name,
#                     'phone': phone,
#                     'email': email,
#                     'bdm': bdm,
#                     'slab': slab,
#                     'source': source,
#                     'state': state,
#                     'service': service,
#                 })

#                 return {
#                     "success": True,
#                     "message": "Lead created successfully",
#                     "lead_id": lead.id
#                 }

#         except Exception as e:
#             return {
#                 "success": False,
#                 "error": str(e)
#             }
