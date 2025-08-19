from odoo import models, fields, api

class PreSalesWizard(models.TransientModel):
    _name = 'pre.sales.wizard'
    _description = 'Pre-Salesperson Selection Wizard'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    pre_salesman_user_id = fields.Many2one('res.users', string="Pre Sales Person",)
    pre_sales_percentage = fields.Float(
        string="Commission (%)",
        default=lambda self: self._default_pre_sales_percentage()
    )

    @api.model
    def _default_pre_sales_percentage(self):
        return float(self.env['ir.config_parameter'].sudo().get_param('scs_pre_salesperson.pre_sales_percentage', 0.0))


    def apply_pre_salesperson(self):
        if self.sale_order_id:
            self.sale_order_id.write({
                'pre_salesman_user_id': self.pre_salesman_user_id.id,
                'pre_sales_percentage': self.pre_sales_percentage,
            })


    def remove_pre_salesperson(self):
        """ Removes the pre-salesperson and resets commission to 0 """
        if self.sale_order_id:
            self.sale_order_id.write({
                'pre_salesman_user_id': False,
                'pre_sales_percentage': 0.0,
            })
