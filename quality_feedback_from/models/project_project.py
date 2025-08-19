from odoo import api, models, fields, _


class ProjectProject(models.Model):
    _inherit = 'project.project'

    survey_id = fields.Many2one("survey.survey", string="Feedback Form")
    feedback_user_id = fields.Many2one("res.users", "Feedback User")