from odoo import models, fields
from werkzeug.urls import url_encode
from urllib.parse import urlencode



class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    # def action_test_survey(self):
    #     res = super().action_test_survey()
    #     if self._context.get('default_task_id'):
    #         print("res-------1111111---", res)
    #         res.update({'url':res.get('url')+"?%s" % urlencode({'default_task_id': self._context.get('default_task_id')})})
    #         print("res----------", res)
    #     return res

    user_input_ids = fields.One2many('survey.user_input', 'survey_id', string='User responses', readonly=True, groups='survey.group_survey_user,quality_feedback_from.group_quality_user')

    def _create_answer(self, user=False, partner=False, email=False, test_entry=False, check_attempts=True, **additional_vals):
        user_inputs = super(SurveySurvey, self)._create_answer(user=user, partner=partner, email=email, test_entry=test_entry, check_attempts=check_attempts, **additional_vals)
        if user_inputs.task_id:
            user_inputs.project_id = user_inputs.task_id.project_id.id
            user_inputs.customer_id = user_inputs.task_id.partner_id

        return user_inputs