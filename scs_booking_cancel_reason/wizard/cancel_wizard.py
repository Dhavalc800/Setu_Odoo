from odoo import models, fields, api

class CancelWizard(models.TransientModel):
    _name = 'cancel.wizard'
    _description = 'Cancel Confirmation Wizard'

    cancel_id = fields.Many2one(
        'cancel.reason',
        string='Cancel Reason',
        required=True,
    )

    def confirm_cancellation(self):
        context = self.env.context
        active_model = context.get('active_model')
        active_id = context.get('active_id')
        records = self.env[active_model].browse(active_id)
        records.write({'cancellation_reason': self.cancel_id.name, 'state': 'cancel'})
