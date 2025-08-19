from odoo import models, Command


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payment_vals_from_wizard(self, batch_result):
        values = super()._create_payment_vals_from_wizard(batch_result)

        order_ids = self.line_ids.move_id.line_ids.sale_line_ids.order_id
        if order_ids:
            values.update(
                {
                    "sale_order_ids": [Command.link(order.id) for order in order_ids],
                }
            )
        return values
