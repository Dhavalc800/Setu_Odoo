from odoo import models, fields

class DispoLeadType(models.Model):
    _name = 'dispo.lead.type'
    _description = 'Dispo Lead Type'

    name = fields.Char(string="Name")