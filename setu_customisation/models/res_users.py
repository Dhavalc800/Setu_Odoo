from odoo import models, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        # Create the user first
        user = super(ResUsers, self).create(vals)

        # Clear all group memberships first
        user.groups_id = [(6, 0, [])]  # This clears all group memberships

        # Define the groups you want to assign
        internal_user_group = self.env.ref('base.group_user')  # Internal User
        sales_user_group = self.env.ref('sales_team.group_sale_salesman')  # Sales User
        email_marketing_group = self.env.ref('hr.group_hr_user')  # Email Marketing User
        invoice_readonly = self.env.ref('sales_team_security.group_booking_invoice_readonly') #Invoice Readonly
        lead_data = self.env.ref('scs_tatatele_integration.group_tatatele_user')

        # Assign the desired groups
        if internal_user_group:
            user.groups_id += internal_user_group
        if sales_user_group:
            user.groups_id += sales_user_group
        if email_marketing_group:
            user.groups_id += email_marketing_group
        if invoice_readonly:
            user.groups_id += invoice_readonly
        if lead_data:
            user.groups_id += lead_data

        return user
