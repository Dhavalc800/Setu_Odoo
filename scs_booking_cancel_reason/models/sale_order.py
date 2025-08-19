from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cancellation_reason = fields.Char(
        string='Cancellation Reason',
    )

    def action_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Confirmation',
            'res_model': 'cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

