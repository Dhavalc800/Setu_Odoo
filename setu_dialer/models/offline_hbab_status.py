from odoo import models, fields

class OfflineHbabStatus(models.Model):
    _name = 'offline.hbab.status'
    _description = 'Offline HBAB Status'

    name = fields.Char(string="Status Name", required=True)