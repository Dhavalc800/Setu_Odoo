from odoo import api, models, fields, _


class ProjectTask(models.Model):
    _inherit = "project.task"

    checklist_task_ids = fields.Many2many("task.checklist", string="CheckList Items")
    project_team_ids = fields.Many2many(
        "crm.team", string="Project Teams", domain=[("type_team", "=", "project")]
    )
    team_members_ids = fields.Many2many(
        "res.users", string="Assigned users", compute="_compute_team_ids", store=True
    )

    @api.depends("project_team_ids")
    def _compute_team_ids(self):
        for rec in self:
            rec.team_members_ids = [(6, 0, [])]
            if rec.project_team_ids:
                rec.team_members_ids = [
                    user.id for user in rec.project_team_ids.mapped("team_members_ids")
                ]

    @api.onchange('project_team_ids','project_id')
    def onchange_field_name(self):
        user_ids_to_remove = []
        for rec in self.project_team_ids:
            user_ids_to_remove.extend(rec.team_members_ids.ids)
        if user_ids_to_remove:
            for user in self.user_ids.ids:
                if user not in user_ids_to_remove:
                    self.user_ids = [(3, user)]
        else:
            self.user_ids = False

    @api.model_create_multi
    def create(self, vals):
        task = super(ProjectTask, self).create(vals)
        for rec in task:
            if rec.project_id:
                checklist_ids = self.env["task.checklist"].search(
                    [("project_id", "=", rec.project_id.id)]
                )
                rec.write({"checklist_task_ids": [(6, 0, checklist_ids.ids)]})
                rec.checklists.write({'state': 'todo'})
                team_ids = self.env['crm.team'].search(
                    [('id', '=', rec.project_id.team_id.id)])
                rec.write({"project_team_ids": [(6, 0, team_ids.ids)]})
        return task

    def write(self, vals):
        project = super(ProjectTask, self).write(vals)
        var = []
        for rec in self:
            new_checklist = rec.checklist_task_ids.checklist_ids
            previous_checklist = rec.checklists.related_checklist_id
            add_new_checklist = new_checklist - previous_checklist
            remove_checklist = previous_checklist - new_checklist
            for line in add_new_checklist:
                var.append(
                    (
                        0,
                        0,
                        {
                            "name": line.name,
                            "description": line.description,
                            "related_checklist_id": line.id,
                        },
                    )
                )
            if add_new_checklist:
                rec.update({"checklists": var})
            if remove_checklist:
                remove_list = rec.checklists.search(
                    [
                        ("related_checklist_id", "in", remove_checklist.ids),
                        ("projects_id", "=", self.id),
                    ]
                )
                remove_list.unlink()

    @api.depends("checklists", "checklists.state")
    def _compute_progress(self):
        for rec in self:
            total_completed = 0
            for activity in rec.checklists:
                if activity.state in ["cancel", "done", "in_progress"]:
                    total_completed += 1
            if len(rec.checklists):
                rec.progress = float(total_completed) / len(rec.checklists) * 100
