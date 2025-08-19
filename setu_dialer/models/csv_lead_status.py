from odoo import models, fields

class CsvLeadStatus(models.Model):
    _name = 'csv.lead.status'
    _description = 'CSV Lead Status'

    name = fields.Char(string='Name', required=True)
    is_reschedule = fields.Boolean(string='Is Reschedule', default=False)
    is_cancel = fields.Boolean(string='Is Cancel', default=False)