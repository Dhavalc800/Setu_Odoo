from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    """ Removed the margin calculation from purchase order line"""
    @api.depends(
        "price_subtotal", "product_uom_qty", "purchase_price", "commission_status"
    )
    def _compute_margin(self):
        res = super(SaleOrderLine, self)._compute_margin()
        for line in self:
            line.margin = (
                    line.price_subtotal
                    - sum(line.mapped("agent_ids.amount"))
                    - (line.purchase_price * line.product_uom_qty)
            )
        return res

        # order = line.purchase_line_ids.order_id
            # if order:
            #     if len(order.order_line) == 1:
            #         line.margin = (
            #             line.price_subtotal
            #             - line.agent_ids.amount
            #             - (
            #                 order.mapped("order_line").price_unit
            #                 * order.mapped("order_line").product_qty
            #             )
            #         )
            #     else:
            #         product = line.product_id
            #         for purchase_rec in order.mapped("order_line"):
            #             for sale_line in purchase_rec.sale_line_id:
            #                 sale_line.margin = (
            #                     sale_line.price_subtotal
            #                     - sale_line.agent_ids.amount
            #                     - (purchase_rec.price_unit * purchase_rec.product_qty)
            #                 )
            # else:

