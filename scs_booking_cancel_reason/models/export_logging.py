from odoo import api, fields, models


class ExportLogging(models.Model):
    _name = 'export.logging'

    user_id = fields.Many2one(
        'res.users',
        string='User',
    )
    model = fields.Char(
        string='Model',
    )
    created_on = fields.Datetime(
        string='Created on',
    )
