from odoo import models, fields

class HbabDataStatus(models.Model):
    _name = 'hbab.data.status'
    _description = 'HBAB Data Status'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", required=True)
