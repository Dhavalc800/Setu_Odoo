from odoo import _, fields, models


class SalePaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    current_url = fields.Char("Current Url")
