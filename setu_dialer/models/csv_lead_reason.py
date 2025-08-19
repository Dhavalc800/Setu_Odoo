from odoo import models, fields

class CsvLeadReason(models.Model):
    _name = 'csv.lead.reason'
    _description = 'CSV Lead Status'

    name = fields.Char(string='Name', required=True)