from odoo import models, fields

class EmployeeBranch(models.Model):
    _inherit = 'employee.branch'

    company_ids = fields.Many2many(
        'operating.company',
        string="Oprational Companies"
    )