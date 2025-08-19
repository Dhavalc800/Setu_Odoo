from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class CRMTeamProcess(models.Model):
    _name = "crm.team.process"
    _description = "CRM Team Process"
    _inherit = ["mail.thread"]

    name = fields.Char(string="Name", required=True)
    team_id = fields.Many2one("crm.team", string="CRM Team")
    user_id = fields.Many2one(
        "res.users",
        string="Team Leader",
        required=True,
        domain=lambda self: [
            (
                "groups_id",
                "=",
                self.env.ref("sales_team_security.group_sale_team_manager").id,
            )
        ],
        default=lambda self: self.env.user,
    )
    member_ids = fields.Many2many("res.users", string="Team Members", required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submit", "Submit"),
            ("approve", "Approve"),
            ("reject", "Reject"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    commission_id = fields.Many2one("crm.commission")
    invoiced_target = fields.Float(
        string="Invoicing Target",
        help="Revenue target for the current month (untaxed total of confirmed invoices).",
    )

    def action_submit(self):
        """
        Method to submit record
        """
        if not self.commission_id:
            raise ValidationError(
                _("You must add Commission Plan Before Submitting Record")
            )
        self.state = "submit"

    def action_approve(self):
        """
        Action Method for Approval,
        and Create Sales Team with given Values.
        """
        self.state = "approve"
        vals = {
            "name": self.name,
            "user_id": self.user_id.id or False,
            "member_ids": self.member_ids.ids or False,
            "commission_id": self.commission_id.id,
            "use_quotations": True,
            "use_leads": True,
            "use_opportunities": True,
            "invoiced_target": self.invoiced_target,
        }
        crm_team_id = self.env["crm.team"].create(vals)
        if crm_team_id:
            self.team_id = crm_team_id.id
        self.member_ids.write({'commission_id': self.commission_id.id})
        self.user_id.write({'commission_id': self.commission_id.id})

    def action_reject(self):
        """
        Method to reject record
        """
        self.state = "reject"

    def action_view_sales_team(self):
        self.ensure_one()
        action = {
            "res_model": "crm.team",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_id": self.team_id.id,
            "name": self.name,
            "domain": [("id", "=", self.team_id.id)],
        }
        return action

    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft(self):
        if any(team.state != "draft" for team in self):
            raise UserError(_("You can only delete draft records"))
