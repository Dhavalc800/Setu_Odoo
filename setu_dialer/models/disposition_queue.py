from odoo import models, fields

class DispositionQueue(models.Model):
    _name = 'disposition.queue'
    _rec_name = 'lead_id'

    lead_id = fields.Many2one('lead.data.lead', string="Lead")
    campaign_id = fields.Many2one("campaigns.list", string="Campaigns")
    lead_list_id = fields.Many2one("lead.list.data", string="Lead List")
    disposition_id = fields.Many2one('dispo.list.name', string='Disposition')
    call_by = fields.Many2one('res.users', string="Call By")
    disposition_time = fields.Datetime(string='Disposition Time')
    disposition_from = fields.Char(string="Disposition From")