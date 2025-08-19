from odoo import api, fields, models, _


class CustomerSource(models.Model):
    _name = 'customer.source'
    _description = "Customer Source"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char()
    is_active = fields.Boolean(default=True)