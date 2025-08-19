from odoo import fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_so_line_values(self, order):
        so_values = super()._prepare_so_line_values(order)
        so_values.update({"name": "Consultancy Service"})
        return so_values

    def _get_down_payment_description(self, order):
        name = super()._get_down_payment_description(order)
        name = "Consultancy Service"
        return name
