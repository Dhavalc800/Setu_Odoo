from odoo import models, fields, _
from odoo.exceptions import UserError
import base64
import io
import csv

class DeleteLeadsWizard(models.TransientModel):
    _name = 'delete.leads.wizard'
    _description = 'Delete Leads by Phone Wizard'

    lead_list_id = fields.Many2one('lead.list.data', string="Lead List", required=True)
    file = fields.Binary("CSV File", required=True)
    file_name = fields.Char("File Name")

    def action_process_csv(self):
        if not self.file:
            raise UserError(_("Please upload a CSV file."))

        # Decode CSV
        data = base64.b64decode(self.file)
        csv_reader = csv.reader(io.StringIO(data.decode("utf-8-sig")))

        # Read and clean header
        header = next(csv_reader)
        header = [h.strip().lower() for h in header]
        if 'phone' not in header:
            raise UserError(_("CSV must contain a 'phone' column."))

        phone_index = header.index('phone')
        phones = set()

        for row in csv_reader:
            if len(row) > phone_index:
                phone = row[phone_index].strip()
                if phone:
                    phones.add(phone)
                    print("\n\nPhone number found:", phone)

        if not phones:
            raise UserError(_("No valid phone numbers found."))

        # Search for leads to delete
        leads_to_delete = self.env['lead.data.lead'].search([
            ('lead_list_id', '=', self.lead_list_id.id),
            ('x_phone', 'in', list(phones)),
            ('lead_usage_status', '!=', 'used')
        ])

        print("\n\nLeads to delete:", leads_to_delete)

        if not leads_to_delete:
            raise UserError(_("No matching leads found in the selected lead list."))

        count = len(leads_to_delete)
        leads_to_delete.unlink()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Done"),
                'message': _("%d leads deleted." % count),
                'type': 'success',
                'sticky': False,
            }
        }

