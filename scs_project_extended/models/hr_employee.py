# Copyright 2018 ForgeFlow, S.L.
# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    date_of_join = fields.Date(string="Date of Join")
    identification_no = fields.Char(string="Identification No")
    l10n_in_pan = fields.Char(related="work_contact_id.l10n_in_pan", string="PAN Card", readonly=False)
    identification_id = fields.Char(string="Aadhar Card")
    salary = fields.Float(string='salary',)
    branch_id = fields.Many2one(
        'employee.branch',
        string='Employee Branch',
    )




class EmployeeBranch(models.Model):
    _name = 'employee.branch'

    name = fields.Char(
        string='Name',
    )
