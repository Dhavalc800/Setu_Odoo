from odoo import models, fields
from odoo.fields import Command


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_view_agreement(self):
        action = super().action_view_agreement()
        action['context'] = {'create': False}
        return action

    def create_agreement(self):
        agreement_obj = self.env["agreement"]
        agreement_line_obj = self.env["agreement.line"]
        name = self.name + "-" + self.partner_id.name
        agreement_state = self.env['agreement.stage'].search([('name', '=', 'Welcome Call Rm')])
        agreement = agreement_obj.create(
            {
                "name": name,
                # "description": agreement_lines.agreement_template_id.name,
                # "agreement_template": agreement_lines.agreement_template_id.agreement_template,
                "sale_id": self.id,
                "partner_id": self.partner_id.id,
                # "agreement_type_id": agreement_lines.agreement_template_id.agreement_type_id.id,
                "booking_date": fields.Datetime.now(),
                "operating_company_id": self.operating_company_id.id or False,
                "stage_id": agreement_state.id,
            }
        )

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
                        "operating_company_id": line.order_id.operating_company_id.id,
                        "stage_id": 20,
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
                        "tax_id": [Command.set(line.tax_id.ids)],
                        "is_refund": line.is_refund,
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
                        "tax_id": [Command.set(line.tax_id.ids)],
                        "is_refund": line.is_refund,
                    }
                )
                line.order_id.agreement_id = agreement.id

