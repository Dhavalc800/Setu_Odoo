from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    operating_company_ids = fields.Many2many(
        related="company_id.operating_company_ids",
        string="Opearting Company",
        readonly=False,
    )
