# See LICENSE file for full copyright and licensing details.

from odoo import fields, models
import threading


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_auto_change_manager_setting = fields.Boolean(
        string="Change Manager", implied_group='project_team.group_auto_change_manager_setting')


class CrmTeamInherit(models.Model):
    _inherit = "crm.team"

    type_team = fields.Selection(
        [("sale", "Sale"), ("project", "Project")], string="Type", default="sale"
    )
    team_members_ids = fields.Many2many(
        "res.users",
        "project_team_user_rel",
        "team_id",
        "user_id",
        "Project Members",
        help="""Project's members are users who can have an access to the tasks related
                                     to this project.""",
    )

    def write(self, vals):
        res = super().write(vals)

        if 'favorite_user_ids' in vals or 'name' in vals:
            thread = threading.Thread(target=self.team_updates, args=(vals,))
            thread.start()
            thread.join()
        return res

    def team_updates(self, vals):
        user_ids = [user_tuple[1] for user_tuple in vals.get('favorite_user_ids', []) if user_tuple[0] == 4]
        new_user_ids = self.crm_team_member_ids.mapped('user_id.id')
        all_users = list(set(user_ids + list(new_user_ids)))

        if all_users:
            users = self.env['res.users'].browse(all_users)
            orders = self.env['sale.order'].search([('user_id', 'in', all_users),('name', '=ilike', 'S%')])
            leads = self.env['crm.lead'].search([('user_id', 'in', all_users)])
            employees = self.env['hr.employee'].search([('user_id', 'in', all_users)])
            parent_employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)])
            change_manager = self.env.user.has_group('project_team.group_auto_change_manager_setting')
            if parent_employee and employees and change_manager:
                employees_to_update = employees.filtered(lambda emp: emp.id != parent_employee.id)
                if employees_to_update:
                    employees_to_update.sudo().write({'parent_id': parent_employee.id, 'coach_id': parent_employee.id})
            if orders:
                orders.sudo().write({'team_id': self.id})
                orders.partner_id.sudo().write({'team_id': self.id})
                invoices = orders.mapped('invoice_ids')
                if invoices:
                    invoices.sudo().write({'team_id': self.id})
            if leads:
                leads.sudo().write({'team_id': self.id})

