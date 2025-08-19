from odoo import models, fields, api

class AgreementFeedbackWizard(models.TransientModel):
    _name = 'agreement.feedback.wizard'
    _description = 'Set Feedback User on Agreement'

    user_id = fields.Many2one('res.users', string="Feedback User ID", required=True)

    def action_apply_feedback_user(self):
        active_ids = self.env.context.get('active_ids')
        agreements = self.env['agreement'].browse(active_ids)
        for agreement in agreements:
            agreement.assign_id = self.user_id.id
