from odoo import models, fields


class AgreementLine(models.Model):
    _inherit = 'agreement.line'

    is_refund = fields.Boolean("Is Refund")
    company_currency_id = fields.Many2one(related='sale_line_id.company_id.currency_id')
    amount_received = fields.Monetary(related="sale_line_id.amount_received", string="Amount received", currency_field='company_currency_id')
    tax_id = fields.Many2many('account.tax', string='Tax')
