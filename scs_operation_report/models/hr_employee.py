from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if self._context.get("is_employee") and not self._context.get("is_domain_updated"):
            rules = self.env.ref('hr_config.hr_employee_rule_user', raise_if_not_found=False)
            if self._context.get("task_id"):
                task_id = self.env["project.task"].browse([self._context.get("task_id")])
                if task_id:
                    employee_ids = [emp.sudo().employee_id.id for emp in task_id.user_ids]
                    args += [("id", "in", task_id.user_ids.sudo().mapped('employee_ids').ids)]
                    if task_id.user_ids and not all(employee_ids):
                        raise UserError(
                            _(
                                "Select Assignees in Task Does not linked with Employee. \nPlease Request your Administrator to Create Employee for Assigned Users."
                            )
                        )
            if self.user_has_groups('project.group_project_user') and not self.user_has_groups(
                    'project_config.group_project_manager_custom') and not self.user_has_groups(
                    'project.group_project_manager'):
                args += [('id', '=', self.env.user.employee_ids.ids)]
            if self.user_has_groups('project_config.group_project_manager_custom') and not self.user_has_groups('project.group_project_manager'):
                team_member = self.env['crm.team'].search([('user_id', '=', self.env.user.id)]).mapped('team_members_ids')
                args += ['|', ("id", "in", team_member.sudo().mapped('employee_ids').ids), ("user_id", "=", self.env.user.id)]
            self.env.context = dict(self.env.context)
            self.env.context.update({
                "is_domain_updated": True
            })
            return super(HrEmployee, self).sudo().with_context(skip_record_rule=True)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)
        return super(HrEmployee, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)
