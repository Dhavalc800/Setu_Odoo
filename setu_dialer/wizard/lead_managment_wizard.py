from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import xlrd
import csv
import io
import datetime

class LeadUploadWizard(models.TransientModel):
    _name = 'lead.upload.wizard'
    _description = 'Upload Leads from Excel or CSV'

    file = fields.Binary("Upload File")
    file_name = fields.Char("File Name")

    format_file = fields.Binary("Format File", readonly=True)
    format_file_name = fields.Char("Format File Name")

    def action_upload(self):
        if not self.file_name:
            raise UserError("Please upload a file.")

        file_extension = self.file_name.lower().split('.')[-1]
        data = base64.b64decode(self.file)

        if file_extension == 'xls':
            workbook = xlrd.open_workbook(file_contents=data)
            sheet = workbook.sheet_by_index(0)
            for row in range(1, sheet.nrows):
                employee_id = str(sheet.cell(row, 0).value).strip()
                phone = str(sheet.cell(row, 6).value).strip()
                if not phone:
                    continue

                # Search employee by identification_no
                employee = self.env['hr.employee'].search([('identification_no', '=', employee_id)], limit=1)

                existing = self.env['lead.management'].search([('phone', '=', phone)], limit=1)
                if existing:
                    continue
                date_str = str(sheet.cell(row, 4).value).strip()  # Example: "17/05/2025"
                parsed_date = False
                try:
                    parsed_date = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
                except:
                    pass
                self.env['lead.management'].create({
                    'name': sheet.cell(row, 1).value,
                    'dispostion_id': False,
                    'datetime': False,
                    'date': parsed_date,
                    'time_slot': sheet.cell(row, 5).value,
                    'email': sheet.cell(row, 6).value,
                    'phone': phone,
                    'slab': sheet.cell(row, 8).value,
                    'service': sheet.cell(row, 9).value,
                    'source': sheet.cell(row, 10).value,
                    'type': sheet.cell(row, 11).value,
                    'city': sheet.cell(row, 12).value,
                    'lead_type': sheet.cell(row, 13).value,
                    'sale_person_name': sheet.cell(row, 14).value,
                    'remarks': sheet.cell(row, 15).value,
                    'user_id': employee.user_id.id if employee  else self.env.uid,
                })

        elif file_extension == 'csv':
            file_io = io.StringIO(data.decode("utf-8"))
            reader = csv.reader(file_io)
            next(reader)
            for row in reader:
                if not row or len(row) < 16 or not row[7].strip():  # phone at index 7
                    continue

                employee_id = row[0].strip()
                phone = row[7].strip()

                # Search employee by identification_no
                employee = self.env['hr.employee'].search([('identification_no', '=', employee_id)], limit=1)
                existing = self.env['lead.management'].search([('phone', '=', phone)], limit=1)
                if existing:
                    continue

                date_str = row[4].strip()  # Example: "17/05/2025"
                parsed_date = False
                try:
                    parsed_date = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
                except:
                    pass
                # lead_id = self.env['lead.management'].search([('name', '=', row[1])], limit=1)
                self.env['lead.management'].create({
                    'name': row[1],
                    'dispostion_id': False,
                    'datetime': False,
                    'date': parsed_date,
                    'time_slot': row[5],
                    'email': row[6],
                    'phone': phone,
                    'slab': row[8],
                    'service': row[9],
                    'source': row[10],
                    'type': row[11],
                    'city': row[12],
                    'lead_type': row[13],
                    'sale_person_name': row[14],
                    'remarks': row[15],
                    'user_id': employee.user_id.id if employee else self.env.uid,
                })
