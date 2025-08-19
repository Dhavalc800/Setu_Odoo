from odoo.addons.survey.controllers.main import Survey
from odoo import http
from odoo.http import request
from odoo.addons.base.models.ir_qweb import keep_query


class SurveySurvey(Survey):
    """over write method to add contex """
    @http.route('/survey/test/<string:survey_token>', type='http', auth='user', website=True)
    def survey_test(self, survey_token, **kwargs):
        survey_sudo, dummy = self._fetch_from_access_token(survey_token, False)
        try:
            answer_sudo = survey_sudo.with_context(default_task_id = kwargs.get("default_task_id"))._create_answer(user=request.env.user, test_entry=True)
        except:
            return request.redirect('/')
        return request.redirect('/survey/start/%s?%s' % (survey_sudo.access_token, keep_query('*', answer_token=answer_sudo.access_token)))
