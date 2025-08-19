from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    sale_order_ids = fields.Many2many(
        "sale.order",
        string="Sale Order Ref",
    )
