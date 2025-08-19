from odoo import api, fields, models, _
from odoo.exceptions import UserError



class SalePersonCollection(models.TransientModel):
    _name = "sale.person.collection.wizard"
    _description = "Sale Person Collection Wizard"

    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)
    refund = fields.Integer(
        string='Refund(%)',
    )

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                # Check if date_from is after date_to
                if record.date_from > record.date_to:
                    raise UserError("The 'Date From' cannot be after the 'Date To'!")

                # # Check if date_from and date_to are in the same month and year
                # if (record.date_from.month != record.date_to.month or
                #         record.date_from.year != record.date_to.year):
                #     raise UserError("The 'Date From' and 'Date To' must be in the same month!")

    def fetch_data(self):
        return self.env["sale.person.collection.report"].sale_person_collection_report(
            self.date_from, self.date_to, self.refund)
