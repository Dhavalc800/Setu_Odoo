# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CreateAgreementWizard(models.TransientModel):
    _name = "create.sale.agreement.wizard"
    _description = "Create Sale Agreement Wizard"

    agreement_template = fields.Selection([("final_sisfs_stages", "Final SISFS_Stages"),
                                           ("consultancy_service_Agreement_naiff", "Consultancy Service Agreement_NAIFF"),
                                           ("consultancy_service_agreement_gg", "Consultancy Service Agreement GG")], required=True, default="final_sisfs_stages")
    
    name = fields.Char(string="Description", required=True)

    def _create_agreement(self):
        self.ensure_one()
        sale_order = self.env['sale.order'].browse(self._context.get('sale_id'))
        name = sale_order.name + "-" + sale_order.partner_id.name 
        agreement = self.env['agreement'].create(
            {
                "name": name,
                "description": self.name,
                "agreement_template": self.agreement_template,
                "sale_id": sale_order.id,
                "partner_id": sale_order.partner_id.id
            } 
        )
        for line in sale_order.order_line.filtered(lambda l: not l.display_type):
                    self.env["agreement.line"].create({
            "product_id": line.product_id.id,
            "name": line.name,
            "agreement_id": agreement.id,
            "qty": line.product_uom_qty,
            "is_refund": line.is_refund,
            "sale_line_id": line.id,
            "uom_id": line.product_uom.id,
            "price_unit":line.price_unit,
            "price_subtotal": line.price_subtotal
        })
        return agreement

    def create_agreement(self):
        agreement = self._create_agreement()
        return agreement.action_view_agreement(agreement)
