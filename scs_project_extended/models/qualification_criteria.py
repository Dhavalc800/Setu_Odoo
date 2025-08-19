from odoo import api, fields, models


class QualificationCriteria(models.Model):
    _name = "qualification.criteria"
    _description = "Qualification Criteria"

    name = fields.Char()
    criteria_ans = fields.Selection([("yes", "Yes"), ("no", "No")], string="Answer")
    task_id = fields.Many2one("project.task")
    project_id = fields.Many2one("project.project")
    releted_criteria_id = fields.Many2one("qualification.criteria", ondelete="cascade")
