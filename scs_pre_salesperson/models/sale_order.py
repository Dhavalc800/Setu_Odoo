from odoo import fields, models
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    pre_salesman_user_id = fields.Many2one(
        'res.users',
        string='Pre Sales Person',
        tracking=True
    )

    pre_sales_percentage = fields.Float(
        string="Pre-Sales Commission (%)",
    )

    def pre_salesperson_wizard(self):
        return {
            "name": "Add Pre-Salesperson Percentage",
            "type": "ir.actions.act_window",
            "res_model": "pre.sales.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_sale_order_id": self.id,
                "default_pre_salesman_user_id": self.pre_salesman_user_id.id,
            },
        }

