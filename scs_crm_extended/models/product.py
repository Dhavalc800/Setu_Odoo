from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class Product(models.Model):
    _inherit = "product.template"

    min_price = fields.Float("Min Product Price")

    @api.constrains("min_price", "list_price")
    def check_product_price(self):
        for rec in self:
            if rec.list_price < rec.min_price or rec.min_price <= 0:
                raise ValidationError(
                    _(
                        "Min price value should be more than 0"
                        if rec.min_price <= 0
                        else "Sale Price amount should be more than minimum product price"
                    )
                )
