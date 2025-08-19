# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    agreement_id = fields.Many2one(
        comodel_name="agreement",
        string="Agreement",
        ondelete="restrict",
        tracking=True,
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
    )

    agreement_type_id = fields.Many2one(
        comodel_name="agreement.type",
        string="Agreement Type",
        ondelete="restrict",
        tracking=True,
        readonly=True,
        copy=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
    )

    # def action_confirm(self):
    #     res = super().action_confirm()
    #     for order in self:
    #         if not order.agreement_id:
    #             order.create_agreement()
    #     return res

    def action_done(self):
        res = super().action_done()
        for order in self:
            if not order.agreement_id:
                order.create_agreement()
        return res

    def create_agreement(self):
        agreement_obj = self.env["agreement"]
        agreement_line_obj = self.env["agreement.line"]
        name = self.name + "-" + self.partner_id.name
        for line in self.order_line.filtered(
            lambda l: not l.display_type and l.product_id.pack_ok
        ):
            if any(
                pack_line.product_id != line.product_id
                for pack_line in line.product_id.pack_line_ids
            ):
                agreement_lines = line.product_id.agreement_line_ids.filtered(
                    lambda al: al.max_agreement_amount >= line.price_subtotal
                    and al.min_agreement_amount < line.price_subtotal
                )
                agreement = agreement_obj.create(
                    {
                        "name": name,
                        "description": agreement_lines.agreement_template_id.name,
                        "agreement_template": agreement_lines.agreement_template_id.agreement_template,
                        "sale_id": line.order_id.id,
                        "partner_id": line.order_id.partner_id.id,
                        "agreement_type_id": agreement_lines.agreement_template_id.agreement_type_id.id,
                    }
                )
                agreement_line_obj.create(
                    {
                        "product_id": line.product_id.id,
                        "name": line.name,
                        "agreement_id": agreement.id,
                        "qty": line.product_uom_qty,
                        "sale_line_id": line.id,
                        "uom_id": line.product_uom.id,
                        "price_unit": line.price_unit,
                        "price_subtotal": line.price_subtotal,
                    }
                )
                line.order_id.agreement_id = agreement.id
        order_lines = self.order_line.filtered(lambda x: x.pack_parent_line_id)
        for line in self.order_line.filtered(lambda l: not l.display_type):
            if line not in order_lines and not line.product_id.pack_ok:
                agreement_lines = line.product_id.agreement_line_ids.filtered(
                    lambda al: al.max_agreement_amount >= line.price_subtotal
                    and al.min_agreement_amount < line.price_subtotal
                )
                agreement = agreement_obj.create(
                    {
                        "name": name,
                        "description": agreement_lines.agreement_template_id.name,
                        "agreement_template": agreement_lines.agreement_template_id.agreement_template,
                        "sale_id": line.order_id.id,
                        "partner_id": line.order_id.partner_id.id,
                        "agreement_type_id": agreement_lines.agreement_template_id.agreement_type_id.id,
                    }
                )
                agreement_line_obj.create(
                    {
                        "product_id": line.product_id.id,
                        "name": line.name,
                        "agreement_id": agreement.id,
                        "qty": line.product_uom_qty,
                        "sale_line_id": line.id,
                        "uom_id": line.product_uom.id,
                        "price_unit": line.price_unit,
                        "price_subtotal": line.price_subtotal,
                    }
                )
                line.order_id.agreement_id = agreement.id

