# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EmpLevel(models.Model):

    """ class for employee level """

    _name = 'hr.emp.level'
    _description = "Employee Level"

    name = fields.Char('Level')
    code = fields.Char('Code')
    parent_id = fields.Many2one('hr.emp.level', 'Parent')
    company_id = fields.Many2one('res.company', 'Company')
    emp_ids = fields.One2many('hr.employee', 
            'level_id', 'Employees')

    @api.constrains('parent_id')
    def _check_parent_id(self):
        for rec in self:
            if not rec._check_recursion():
                raise ValidationError(
                    _('Error! You can not create recursive hierarchy of record(s).'))

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    level_id = fields.Many2one('hr.emp.level', 'Level')