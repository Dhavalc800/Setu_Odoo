from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    operating_company_id = fields.Many2one(
        "operating.company", string="Operating Company", copy=False
    )
    einvoice_status = fields.Selection(
        [
            ("pending", "Payment Pending"),
            ("invoice_pending", "Invoice Pending"),
            ("completed", "Completed"),
            ("incomplete", "Incomplete"),
        ],
        default="pending",
        string="E-invoice Status",
    )
    status_updated_by = fields.Char(string='Status Updated By')


    @api.model_create_multi
    def create(self, vals_list):
        records = super(AccountMove, self).create(vals_list)
        for rec in records.filtered(lambda l: l.operating_company_id):
            rec.write(
                {
                    "name": rec.env["ir.sequence"].next_by_code(
                        rec.operating_company_id.sequence_id.code
                    )
                }
            )
        return records

    def write(self, vals):
        res = super().write(vals)
        if "einvoice_status" in vals:
            self.write({'status_updated_by': self.env.user.name})
        return res

    @api.depends("bank_partner_id", "operating_company_id")
    def _compute_partner_bank_id(self):
        super()._compute_partner_bank_id()
        for move in self:
            if move.operating_company_id.partner_id.bank_ids:
                move.partner_bank_id = move.operating_company_id.partner_id.bank_ids[0]
