# Copyright 2019 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class BaseSubstateType(models.Model):
    _inherit = "base.substate.type"

    model = fields.Selection(
        selection_add=[("sale.order", "Sale order")], ondelete={"sale.order": "cascade"}
    )


class SaleOrder(models.Model):
    _inherit = ["sale.order", "base.substate.mixin"]
    _name = "sale.order"

    @api.constrains("substate_id", "state")
    def check_substate_id_value(self):
        sale_states = dict(self._fields["state"].selection)
        for order in self:
            target_state = order.substate_id.target_state_value_id.target_state_value
            if order.substate_id and order.state != target_state:
                raise ValidationError(
                    _(
                        "The substate %(name)s is not defined for the state"
                        " %(state)s but for %(target_state)s "
                    )
                    % {
                        "name": order.substate_id.name,
                        "state": _(sale_states[order.state]),
                        "target_state": _(sale_states[target_state]),
                    }
                )

    def _track_template(self, changes):
        res = super(SaleOrder, self)._track_template(changes)
        track = self[0]
        if "substate_id" in changes and track.substate_id.mail_template_id:
            res["substate_id"] = (
                track.substate_id.mail_template_id,
                {
                    "composition_mode": "comment",
                    "auto_delete_message": True,
                    "message_type": 'notification',
                    "subtype_id": self.env["ir.model.data"]._xmlid_to_res_id(
                        "mail.mt_note"
                    ),
                    "email_layout_xmlid": "mail.mail_notification_light",
                    "partner_ids": [(6,0, self._get_users_emails())]
                },
            )
        return res

    def _get_users_emails(self):
        self.ensure_one()
        user_ids = []
        if self.substate_id.sending_mail == "group":
            user_ids = self.substate_id.group.users.mapped("partner_id.id")
            # emails = ",".join(str(e) for e in user_ids if e)
            return user_ids
        else:
            return [self.user_id.partner_id.id]

    def payment_received(self):
        self.write(
            {
                "substate_id": self.env.ref(
                    "base_substate.base_substate_payment_received", raise_if_not_found=False
                ).id
            }
        )

    def request_payment_verification(self):
        self.write(
            {
                "substate_id": self.env.ref(
                    "base_substate.base_substate_payment_verification", raise_if_not_found=False
                ).id
            }
        )

    is_payment_received = fields.Boolean(
        compute="_compute_is_payment_received", string="Is Payment Received", store=True
    )

    is_payment_verification = fields.Boolean(
        compute="_compute_is_payment_verification",
        string="Is Payment Verification",
        store=True,
    )

    @api.depends("substate_id")
    def _compute_is_payment_received(self):
        for record in self:
            record.is_payment_received = False
            # if record.substate_id.id in [
            #     self.env.ref(
            #         "base_substate.base_substate_request_payment_verification"
            #     ).id,
            #     self.env.ref("base_substate.base_substate_payment_received").id,
            # ]:
            #     record.is_payment_received = True

    @api.depends("substate_id")
    def _compute_is_payment_verification(self):
        for record in self:
            record.is_payment_verification = False
            # if self.env.ref("base_substate.base_substate_request_payment_verification"):
            #     if (
            #         record.substate_id.id
            #         == self.env.ref(
            #             "base_substate.base_substate_request_payment_verification"
            #         ).id
            #     ):
            #         record.is_payment_verification = True
