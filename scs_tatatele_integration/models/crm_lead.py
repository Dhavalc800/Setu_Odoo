from odoo import api, fields, models


class Lead(models.Model):
    _inherit = 'crm.lead'

    client_number = fields.Char("Client Number")
    call_details = fields.Many2one('call.record.details', "Call record detail")
