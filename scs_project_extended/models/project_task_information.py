from odoo import api, fields, models


class ProjectTaskInformation(models.Model):
    _name = "project.task.information"
    _description = "Project Task Information"

    name = fields.Char()
    type_of_field = fields.Selection(
        [
            ("text", "Text"),
            ("date", "Date"),
            ("integer", "Integer"),
            ("float", "Float"),
        ],
        required=True,
    )
    text_value = fields.Char()
    date_value = fields.Date()
    integer_value = fields.Integer()
    float_value = fields.Float()
    task_id = fields.Many2one("project.task", ondelete="cascade")
    project_id = fields.Many2one("project.project", ondelete="cascade")
    information = fields.Char(compute="compute_information")
    related_information_id = fields.Many2one(
        "project.task.information", ondelete="cascade"
    )

    @api.depends("text_value", "date_value", "integer_value", "float_value")
    def compute_information(self):
        self.information = ""
        for rec in self:
            if rec.text_value:
                rec.information = rec.text_value
            if rec.date_value:
                rec.information = str(rec.date_value)
            if rec.integer_value:
                rec.information = str(rec.integer_value)
            if rec.float_value:
                rec.information = str(rec.float_value)
