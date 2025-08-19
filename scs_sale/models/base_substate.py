from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "base.substate"

    groups_ids = fields.Many2many('res.groups', string='Groups')
