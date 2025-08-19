from odoo import fields, models

class IndustrySector(models.Model):
    _name = "industry.sector"
    _description = "Industry Sector"

    name = fields.Char()
    industry_id = fields.Many2one("res.partner.industry")

