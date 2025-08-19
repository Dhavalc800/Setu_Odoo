# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    agreement_template_id = fields.Many2one(
        "agreement", string="Agreement Template", domain="[('is_template', '=', True)]"
    )

    action_view_agreement_count = fields.Integer(compute="_compute_agreement")
    booking_type = fields.Selection(
        [
            ("normal", "Normal"),
            ("normal_combo", "Normal Combo"),
            ("hbab", "HBAB"),
        ],
        copy=False
    )

    def _compute_agreement(self):
        for agreement in self:
            self.action_view_agreement_count = self.env["agreement"].search_count([('sale_id', '=', agreement.id)])

    def action_view_agreement(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "agreement.agreement_action"
        )
        agreement = self.env["agreement"].search([("sale_id", "=", self.id)])
        if len(agreement) > 1:
            action["domain"] = [("id", "in", agreement.ids)]
        elif len(agreement) == 1:
            form_view = [
                (self.env.ref("agreement_legal.partner_agreement_form_view").id, "form")
            ]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = agreement.id
        return action
