from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    operating_company_ids = fields.Many2many(
        "operating.company",
        string="Operating Company",
        copy=False,
    )
