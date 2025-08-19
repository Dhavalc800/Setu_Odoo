from odoo import api, fields, models, _


class DispositionListConfiguration(models.Model):
    _name = 'disposition.list.configuration'
    _description = "Disposition List Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Disposition", tracking=True)
    disposition_ids = fields.Many2many(
        'dispo.list.name',
        'campaigns_disposition_rel',
        'campaign_id',
        'disposition_id',
        tracking=True,
        string="Dispo Name"
    )