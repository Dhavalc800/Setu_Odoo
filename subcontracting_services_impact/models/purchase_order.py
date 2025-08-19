from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        result = super(PurchaseOrder, self).button_confirm()
        for order in self:
            commission_total_so = order.order_line.mapped(
                "sale_order_id"
            ).order_line.agent_ids._compute_amount()
            margin = (
                order.order_line.mapped("sale_order_id")
                .mapped("order_line")
                ._compute_margin()
            )
