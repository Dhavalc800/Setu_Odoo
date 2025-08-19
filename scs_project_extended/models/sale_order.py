from odoo import fields, models, api
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tasks_count = fields.Integer(
        string='Tasks', compute='_compute_tasks_ids', groups="base.group_user")
    project_count = fields.Integer(
        string='Number of Projects', compute='_compute_project_ids', groups="base.group_user")
    related_phone = fields.Char(string='mobile', related='partner_id.mobile')
    related_email = fields.Char(string='email', related='partner_id.email')

    def action_view_task(self):
        self.ensure_one()

        list_view_id = self.env.ref('project.view_task_tree2').id
        form_view_id = self.env.ref('project.view_task_form2').id

        action = {'type': 'ir.actions.act_window_close'}
        task_projects = self.tasks_ids.mapped('project_id')
        # redirect to task of the project (with kanban stage, ...)
        if len(task_projects) == 1 and len(self.tasks_ids) > 1:
            action = self.with_context(active_id=task_projects.id).env['ir.actions.actions']._for_xml_id(
                'project.act_project_project_2_project_task_all')
            if action.get('context'):
                eval_context = self.env['ir.actions.actions']._get_eval_context(
                )
                eval_context.update({'active_id': task_projects.id})
                action_context = safe_eval(action['context'], eval_context)
                action_context.update(eval_context)
                action['context'] = action_context
        else:
            action = self.env["ir.actions.actions"]._for_xml_id(
                "scs_project_extended.action_view_task_no_edit")
            if self.env.user.has_group("project.group_project_manager") or self.env.user.has_group(
                    "project_config.group_project_coordinator") or self.env.user.has_group("project_config.group_project_manager_custom") or self.env.user.has_group("project.group_project_user"):
                action = self.env["ir.actions.actions"]._for_xml_id(
                    "project.action_view_task")
            # erase default context to avoid default filter
            action['context'] = {}
            if len(self.tasks_ids) > 1:  # cross project kanban task
                action['views'] = [[False, 'kanban'], [list_view_id, 'tree'], [
                    form_view_id, 'form'], [False, 'graph'], [False, 'calendar'], [False, 'pivot']]
            elif len(self.tasks_ids) == 1:  # single task -> form view
                action['views'] = [(form_view_id, 'form')]
                action['res_id'] = self.tasks_ids.id
        # filter on the task of the current SO
        action['domain'] = [('id', 'in', self.tasks_ids.ids)]
        action.setdefault('context', {})
        if action and action.get('xml_id') and action.get('xml_id') == "scs_project_extended.action_view_task_no_edit":
            action.update({
                'context': dict(self.env.context, edit=False)
            })
        return action
    
    @api.depends("state")
    def action_cancel(self):
        # First, call the original action_cancel method
        res = super(SaleOrder, self).action_cancel()

        if self.tasks_ids:
            for task in self.tasks_ids:
                task.write({'active': False})
        return res