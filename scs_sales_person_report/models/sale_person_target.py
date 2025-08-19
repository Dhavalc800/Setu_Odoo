from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class SalePersonTarget(models.Model):
    _name = "sale.person.target"
    _description = "Sale Person Target"

    company_id = fields.Many2one("res.company")
    name = fields.Char("Reference")
    start_date = fields.Date("Start Date", default=datetime.today().replace(day=1), required="1")
    end_date = fields.Date("End Date", default=datetime(datetime.today().year, datetime.today().month, 1) + relativedelta(months=1, days=-1), required="1")
    state = fields.Selection([('draft', "Draft"), ('review', "Review"), ('confirm', "Confirm"), ('cancel', "Cancel")], string="State",
                             default='draft')
    sale_person_target_line_ids = fields.One2many("sale.person.target.line", "sale_person_target_id", string="Sale Person Target Lines")

    def confirm_sale_person_target(self):
        for record in self:
            record.state = 'confirm'

    def cancel_sale_person_target(self):
        for record in self:
            record.state = 'cancel'

    def review_sale_person_target(self):
        for record in self:
            if not record.sale_person_target_line_ids:
                raise UserError(_("Please Add Sale Person Target Lines"))
            record.state = 'review'

    def set_to_draft(self):
        for record in self:
            record.state = 'draft'

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date > record.end_date:
                raise UserError(_("End Date Must be Greater then Start Date"))
            start_month = record.start_date.strftime('%Y-%m')
            end_month = record.end_date.strftime('%Y-%m')

            domain = [
                ('id', '!=', record.id),
                '|',
                ('start_date', '>=', record.start_date),
                ('start_date', '<=', record.end_date),
                '|',
                ('end_date', '>=', record.start_date),
                ('end_date', '<=', record.end_date),
            ]
            existing_records = self.search(domain)
            for rec in existing_records:
                existing_start_month = rec.start_date.strftime('%Y-%m')
                existing_end_month = rec.end_date.strftime('%Y-%m')
                if start_month == existing_start_month or end_month == existing_end_month:
                    raise ValidationError('Only one record per month is allowed.')

    @api.constrains('sale_person_target_line_ids')
    def _check_user_id(self):
        target_line_user = [rec.user_id for rec in self.sale_person_target_line_ids]
        countOccurrences = lambda lst, x: lst.count(x)
        for record in self.sale_person_target_line_ids:
            if countOccurrences(target_line_user, record.user_id) > 1:
                raise ValidationError(_("You have already added %s", record.user_id.name))

    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft_or_cancel(self):
        if any(record.state not in ('draft', 'cancel') for record in self):
            raise UserError(_('You can only delete draft or cancelled records.'))
