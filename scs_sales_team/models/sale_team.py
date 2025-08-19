from odoo import api, fields, models


class Team(models.Model):
    _inherit = "crm.team"

    branch_boolean = fields.Boolean(
        string='branch boolean',
        compute='_compute_branch_boolean')

    def _compute_branch_boolean(self):
        self.branch_boolean = False
        user_has_group = self.env.user.has_group("sales_team_security.group_booking_branch_manager")
        for record in self:
            if user_has_group:
                record.branch_boolean = True
