from odoo import fields,models
from odoo.exceptions import UserError



class OpenSurvey(models.TransientModel):
    _name='opan.survey'
    _description = 'Open Survey'
    
    survey_id = fields.Many2one("survey.survey", string="Feedback Form", required=True)

    def action_open_survey_from(self):
        return {
            'name': 'Feedback Form',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'survey.survey',
            'res_id': self.survey_id.id,
            'type': 'ir.actions.act_window',
        }