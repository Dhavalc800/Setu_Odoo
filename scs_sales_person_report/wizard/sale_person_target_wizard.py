from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import calendar


class SalePersonTargetWizard(models.TransientModel):
    _name = "sale.person.target.wizard"
    _description = "Sale Person Target Wizard"

    date_from = fields.Date(string="Date From", default=datetime.today().replace(day=1))
    date_to = fields.Date(string="Date To", compute='_compute_end_of_month_date', store=True)

    def fetch_data(self):
        return self.env["sale.person.monthly.target"].sale_person_target_report(
            self.date_from, self.date_to)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from > rec.date_to:
                raise UserError(_("End Date Must be Greater then Start Date"))

    @api.depends('date_from')
    def _compute_end_of_month_date(self):
        for wizard in self:
            if wizard.date_from:
                date_from = fields.Date.from_string(wizard.date_from)
                last_day = calendar.monthrange(date_from.year, date_from.month)[1]
                end_of_month_date = date_from.replace(day=last_day)
                wizard.date_to = end_of_month_date
            else:
                wizard.date_to = False
