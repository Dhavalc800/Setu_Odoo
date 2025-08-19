from odoo import api, fields, models


class Lead(models.Model):
    _inherit = "crm.lead"

    amount = fields.Monetary(
        string="Amount", currency_field="company_currency", compute="compute_amount"
    )
    product_ids = fields.Many2many("product.template", string="Products")
    is_editable = fields.Boolean("Is Editable", compute="compute_is_editable")

    def _get_default_payment_link_values(self):
        self.ensure_one()
        return {
            "description": self.name,
            "amount": self.amount,
            "currency_id": self.company_currency.id,
            "partner_id": self.partner_id.id,
            "amount_max": self.amount,
        }

    @api.depends("product_ids")
    def compute_amount(self):
        total_amount = 0
        for rec in self:
            total_amount = sum(rec.product_ids.mapped("list_price"))
        self.amount = total_amount

    def compute_is_editable(self):
        self.is_editable = (
            self.env.user.has_group("sales_team.group_sale_salesman_all_leads")
            or self.env.user.has_group("sales_team.group_sale_manager")
            or self.env.user.has_group("sales_team_security.group_sale_team_manager")
        )
