from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime


class OperationTaskActivity(models.Model):
    _name = "operation.task.activity"
    _description = "Operation Task Activity"
    _rec_name="operation_activity_id"

    operation_activity_id = fields.Many2one(
        "activity.type.config", string="Operation Activity"
    )
    employee_id = fields.Many2one("hr.employee", string="Employee")
    start_date = fields.Date(string="Start Date", default=datetime.now().date())
    end_date = fields.Date(string="End Date")
    status = fields.Selection(
        [
            ("new", "New"),
            ("inprogress", "In Progress"),
            ("done", "Done"),
            ("cancel", "Cancel"),
        ],
        default="new",
    )
    taken_days = fields.Float("Taken Day's", compute="_compute_taken_days", store=True)
    blocked_by = fields.Char("Blocked By")
    task_id = fields.Many2one("project.task", string="Task")
    project_id = fields.Many2one(
        related="task_id.project_id", store=True, string="Project"
    )
    date_deadline = fields.Date(string="Deadline")
    project_team_ids = fields.Many2many(related="task_id.project_team_ids", string="Project Team")

    @api.depends("start_date", "end_date")
    def _compute_taken_days(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise UserError(_("End Date Must be Greater Than Start Date."))
                rec.taken_days = (rec.end_date - rec.start_date).days

    def write(self, vals):
        if vals.get("status") in ["done", "cancel"]:
            vals.update({"end_date": datetime.now().date()})
        res = super(OperationTaskActivity, self).write(vals)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super(OperationTaskActivity, self).create(vals_list)
        for rec in records:
            if rec.status == "done":
                rec.end_date = datetime.now().date()
        return records

    @api.model
    def taken_days_calculate(self):
        res_ids = self.env["operation.task.activity"].search(
            [("status", "not in", ["done", "cancel"]), ("employee_id", "!=", False)]
        )
        for rec in res_ids:
            rec.taken_days = (fields.Date.today() - rec.start_date).days

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        context = self._context or {}
        if self.user_has_groups('project.group_project_user') and not self.user_has_groups('project_config.group_project_manager_custom') and not self.user_has_groups(
                'project.group_project_manager'):
            args += [('employee_id', '=', self.env.user.employee_ids.ids)]
        if self.user_has_groups('project_config.group_project_manager_custom') and not self.user_has_groups('project.group_project_manager'):
            team_member = self.env['crm.team'].search([('user_id', '=', self.env.user.id)]).mapped('team_members_ids')
            args += ['|',('employee_id', 'in', self.env.user.employee_ids.ids),('employee_id', 'in',team_member.sudo().mapped('employee_ids').ids)]
        return super(OperationTaskActivity, self)._search(args, offset, limit, order, count=count, access_rights_uid=access_rights_uid)
