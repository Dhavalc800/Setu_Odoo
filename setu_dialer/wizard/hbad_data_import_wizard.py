from odoo import models, fields, _
from odoo.exceptions import UserError
import base64
import csv
import io
from datetime import datetime

class HbadDataImportWizard(models.TransientModel):
    _name = 'hbad.data.import.wizard'
    _description = 'Import HBAD Data'

    upload_file = fields.Binary(string="Upload CSV File", required=True)
    filename = fields.Char("Filename")

    def _parse_date(self, date_str):
        """Parses date in DD/MM/YYYY or fallback to YYYY-MM-DD."""
        if not date_str:
            return False
        try:
            return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
        except ValueError:
            try:
                return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
            except ValueError:
                raise UserError(_(f"Invalid date format: '{date_str}'. Expected DD/MM/YYYY or YYYY-MM-DD."))

    def action_import_csv(self):
        if not self.upload_file:
            raise UserError("Please upload a CSV file.")
        
        file_content = base64.b64decode(self.upload_file)
        data = io.StringIO(file_content.decode("utf-8"))
        reader = csv.DictReader(data)

        Product = self.env['product.template']
        Status = self.env['hbab.data.status']
        Model = self.env['hbad.data.info']

        for row in reader:
            product_names = [name.strip() for name in row.get("Products", "").split(",") if name.strip()]

            product_ids = Product.search([('name', 'in', product_names)]).ids
            if product_names and not product_ids:
                print(f"Warning: No matching products found in DB for: {product_names}")

            status_id = Status.search([('name', '=', row.get("Status"))], limit=1).id

            Model.create({
                'date': self._parse_date(row.get("Date")),
                'booking_id': row.get("Booking ID"),
                'allocation_date': self._parse_date(row.get("Allocation Date")),
                'contact_number': row.get("Contact Number"),
                'customer_name': row.get("Customer Name"),
                'structure': row.get("Structure"),
                'product_ids': [(6, 0, product_ids)],
                'location': row.get("Location"),
                'status': status_id,
                'remarks': row.get("Remarks"),
                'brief': row.get("Brief"),
            })

        return {'type': 'ir.actions.act_window_close'}
