from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    agreement_template_id = fields.Many2one(
        "agreement", string="Agreement Template", domain="[('is_template', '=', True)]"
    )
    agreement_line_ids = fields.One2many(
        "agreement.details", "product_id", string="Agreement Lines"
    )
    name = fields.Char('Name', index='trigram', required=True, translate=True, tracking=True)


class AgreementDetails(models.Model):
    _name = "agreement.details"
    _description = 'Agreement Details'

    product_id = fields.Many2one("product.template")
    agreement_template_id = fields.Many2one(
        "agreement", string="Agreement Template", domain="[('is_template', '=', True)]"
    )
    min_agreement_amount = fields.Float("Min Agreement Amount")
    max_agreement_amount = fields.Float("Max Agreement Amount")
