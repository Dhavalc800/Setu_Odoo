# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class TimeSheetType(models.Model):
    _name = 'timesheet.type'
    _description = 'TimeSheetType'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    is_default = fields.Boolean(string='Set Default')
