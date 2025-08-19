from odoo import fields, models, _


class HrJob(models.Model):
    _inherit = "hr.job"

    job_code = fields.Char(string="Job Code")