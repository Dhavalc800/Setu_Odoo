from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"


    def _prepare_confirmation_values(self):
        """Prepare the sales order confirmation values.

        Note: self can contain multiple records.

        :return: Sales Order confirmation values
        :rtype: dict
        """
        self.ensure_one()
        vals = {'state': 'sale'}
        if self.name and self.name.startswith('S'):
            vals['date_order'] = fields.Datetime.now()
        return vals

