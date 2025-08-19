from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64, csv, io

class LeanManualUploadWizard(models.TransientModel):
    _name = 'lean.manual.upload.wizard'
    _description = 'Manual Lead Upload Wizard'

    upload_file = fields.Binary(string="Upload CSV File", required=True)
    file_name   = fields.Char(string="File Name")

    def action_import_csv(self):
        if not self.upload_file:
            raise ValidationError(_("Please upload a CSV file."))

        # decode & read
        data = base64.b64decode(self.upload_file)
        reader = csv.DictReader(io.StringIO(data.decode('utf-8')))

        LeadLine = self.env['lean.manual.lead']
        # get the model record so we can create fields on it
        model = self.env['ir.model'].sudo().search([('model', '=', 'lean.manual.lead')], limit=1)
        if not model:
            raise ValidationError(_("Model lean.manual.lead not found!"))

        # these are the columns we treat as “standard”:
        standard_cols = {
            'employee_id', 'company_name', 'email', 'service', 'bdm',
            'slab', 'phone', 'source', 'state', 'remark',
        }

        for row in reader:
            phone = (row.get('phone') or '').strip()
            if not phone:
                continue
            phone_last10 = phone[-10:]

            # skip duplicates
            if LeadLine.search_count([('phone', 'ilike', phone_last10)]):
                continue

            # map employee by identification_no
            emp_code = row.get('employee_id') or ''
            emp = self.env['hr.employee'].sudo().search([('identification_no', '=', emp_code)], limit=1)
            user_id = emp.user_id.id if emp and emp.user_id else self.env.uid

            # prepare the vals dict with standard fields
            vals = {
                'employee_id':   user_id,
                'company_name':  row.get('company_name'),
                'email':         row.get('email'),
                'service':       row.get('service'),
                'bdm':           row.get('bdm'),
                'slab':          row.get('slab'),
                'phone':         phone,
                'source':        row.get('source'),
                'state':         row.get('state'),
                'remark':        row.get('remark'),
            }

            # collect any extra columns
            extra_lines = []
            for col, val in row.items():
                if col in standard_cols or not col or val is None:
                    continue
                display = col.strip()
                value   = val.strip()
                field_name = 'x_' + display.lower().replace(' ', '_')

                # create the field if it doesn't exist
                existing = self.env['ir.model.fields'].sudo().search([
                    ('model_id', '=', model.id),
                    ('name',     '=', field_name),
                ], limit=1)
                if not existing:
                    self.env['ir.model.fields'].sudo().create({
                        'model_id':         model.id,
                        'name':             field_name,
                        'field_description': display,
                        'ttype':            'char',
                        'state':            'manual',
                    })

                # add to vals and summary
                vals[field_name] = value
                extra_lines.append(f"{display}: {value}")

            # store the dynamic text blobs
            summary = "\n".join(extra_lines)
            vals['dynamic_field_values'] = summary
            vals['dynamic_summary']      = summary

            # finally create the lead
            LeadLine.create(vals)

        # after import, open the tree/form view
        return {
            'type':        'ir.actions.act_window',
            'name':        _('Manually Uploaded Leads'),
            'res_model':   'lean.manual.lead',
            'view_mode':   'tree,form',
            'target':      'current',
        }