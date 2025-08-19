from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_id', 'order_id')
    def _check_duplicate_service_for_customer(self):
        for line in self:
            if line.product_id and line.product_id.type == 'service':
                customer = line.order_id.partner_id
                # Search for existing sale order lines for same service and customer, excluding current line
                existing_lines = self.search([
                    ('product_id', '=', line.product_id.id),
                    ('order_id.partner_id', '=', customer.id),
                    ('id', '!=', line.id)
                ])
                if existing_lines:
                    raise ValidationError(f"The service '{line.product_id.name}' is already added for customer '{customer.name}'.")
    