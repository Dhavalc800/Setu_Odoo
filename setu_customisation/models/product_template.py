from odoo import models, fields, api
from datetime import timedelta

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_seedfund = fields.Boolean("Is Seedfund", tracking=True)