# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    qualification_criteria_ids = fields.One2many(
        "qualification.criteria", "project_id", string="Qualification Criteria"
    )
    task_imformation_ids = fields.One2many(
        "project.task.information", "project_id", string="Task Information"
    )
    project_coordinator_ids = fields.Many2many(
        "res.users",
        "proj_coordinator_rel",
        "project_id",
        "coordinator_id",
        "Project coordinator",
    )
    allow_timesheets = fields.Boolean(
        "Timesheets", compute='_compute_allow_timesheets', store=True, readonly=False,
        default=False)

    auto_assignees = fields.Boolean(string='Auto Assigned')

    def write(self, vals):
        for rec in self:
            var = []
            task_var = []
            previous_line = rec.qualification_criteria_ids
            previous_task_line = rec.task_imformation_ids
            project = super(ProjectProject, self).write(vals)
            new_line = rec.qualification_criteria_ids
            new_task_line = rec.task_imformation_ids
            add_new_line = new_line - previous_line
            add_new_task_line = new_task_line - previous_task_line
            for line in add_new_line:
                var.append(
                    (
                        0,
                        0,
                        {
                            "name": line.name,
                            "releted_criteria_id": line.id,
                            "task_id": False,
                        },
                    )
                )
            for task_line in add_new_task_line:
                task_var.append(
                    (
                        0,
                        0,
                        {
                            "name": task_line.name,
                            "type_of_field": task_line.type_of_field,
                            "related_information_id": task_line.id,
                            "task_id": False,
                        },
                    )
                )

            rec.task_ids.write(
                {
                    "qualification_criteria_ids": var,
                    "task_imformation_ids": task_var,
                }
            )

            return project

    @api.onchange("team_id")
    def onchnege_project_manager(self):
        self.user_id = self.team_id.user_id.id


    def auto_assigned_user_on_task(self):
        projects = self.search([('team_id', '!=', False), ('auto_assignees', '=', True)])
        tasks = self.env['project.task'].search([('project_id', 'in', projects.ids), ('user_ids', '=', False)])
        teams = projects.mapped('team_id')
        for team in teams:
            user_counter = team.user_counter or 0
            users = sorted(team.team_members_ids, key=lambda user: user.id)
            if users:
                for task in tasks:
                    task.write({'user_ids': [(4, users[user_counter].id)]})
                    user_counter = (user_counter + 1) % len(users)
                team.write({'user_counter': user_counter})
        return True


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    user_counter = fields.Integer(string="User Counter", default=0)
