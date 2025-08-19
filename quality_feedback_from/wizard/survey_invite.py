from odoo import models


class SurveyInvite(models.TransientModel):
    _inherit = "survey.invite"

    def action_invite(self):
        res = super(SurveyInvite, self).action_invite()
        quality_rec = self.env['quality.feedback'].search([('task_id', '=', self._context.get('default_task_id'))],
                                                          limit=1)
        if quality_rec.exists():
            quality_rec.write({'state':'confirm'})
        return res
