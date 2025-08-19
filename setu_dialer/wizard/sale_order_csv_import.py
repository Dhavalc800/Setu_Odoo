from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import csv
from io import StringIO
from datetime import datetime

class SaleOrderCSVImport(models.TransientModel):
    _name = 'sale.order.csv.import'
    _description = 'Sale Order CSV Import'

    upload_file = fields.Binary("Upload CSV File", required=True, attachment=False)
    filename = fields.Char()

    def action_process_file(self):
        if not self.upload_file:
            raise UserError(_("Please upload a CSV file."))

        content = base64.b64decode(self.upload_file).decode('utf-8')
        data = csv.DictReader(StringIO(content), delimiter=',')  # expects header: Order Reference, Agreement Status, Agreement Close Date

        for row in data:
            order_ref = row.get('Order Reference')
            agreement_status_name = row.get('Agreement Status')
            close_date_str = row.get('Agreement Close Date')  # e.g., "27/06/2025"

            if not order_ref:
                continue

            order = self.env['sale.order'].search([('name', '=', order_ref)], limit=1)
            if not order:
                continue

            # Find agreement status
            agreement_status = self.env['agreement.status'].search([('name', '=', agreement_status_name)], limit=1)

            # Parse close date if present
            close_date = False
            if close_date_str:
                try:
                    close_date = datetime.strptime(close_date_str.strip(), '%d/%m/%Y').date()
                except Exception:
                    raise UserError(_("Invalid date format for Order %s: %s. Use dd/mm/yyyy.") % (order_ref, close_date_str))

            # Update order
            order.write({
                'agreement_status_id': agreement_status.id if agreement_status else False,
                'agreement_close_date': close_date
            })


# from odoo import models, fields, api, _
# from odoo.exceptions import UserError
# import base64
# import csv
# from io import StringIO

# class SaleOrderCSVImport(models.TransientModel):
#     _name = 'sale.order.csv.import'
#     _description = 'Sale Order CSV Import'

#     upload_file = fields.Binary("Upload CSV File", required=True, attachment=False)
#     filename = fields.Char()

#     def action_process_file(self):
#         if not self.upload_file:
#             raise UserError(_("Please upload a CSV file."))

#         content = base64.b64decode(self.upload_file).decode('utf-8')
#         data = csv.DictReader(StringIO(content), delimiter=',')  # or '\t' if needed

#         for row in data:
#             print("Parsed Row:", row)
#             order_ref = row['Order Reference']
#             funding_month = int(row['Funding Month'])

#             order = self.env['sale.order'].search([('name', '=', order_ref)], limit=1)
#             funding = self.env['funding.service.month'].search([('month_number', '=', funding_month)], limit=1)

#             if order:
#                 order.write({'funding_month_id': funding.id if funding else False})

