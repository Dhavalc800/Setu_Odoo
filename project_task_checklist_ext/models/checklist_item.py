from odoo import models, fields, api, _


class ChecklistItem(models.Model):
    _inherit = 'checklist.item'

    related_checklist_id = fields.Many2one("checklist.item")
