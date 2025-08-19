from odoo import api, fields, models, _


class ProjectTaskAssignees(models.TransientModel):
    _name = 'project.task.assignees'
    _description = "Add Assignees on project task"



    user_ids = fields.Many2many(
        'res.users',
        string='Assignees',
        domain="[('id', 'in', team_member_ids)]"
    )
    project_team_id = fields.Many2one(
        'crm.team',
        string='Project Team',
        required=True
    )
    team_member_ids = fields.Many2many(
        'res.users',
        string="Team Members",
        compute="_compute_team_member_ids",
        store=False
    )
    stage_id = fields.Many2one(
        'project.task.type',
        string='Stage',
        domain="[('id', 'in', default_stage_ids)]",
    )
    default_stage_ids = fields.Many2many(
        'project.task.type',
        string='Stage',
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super(ProjectTaskAssignees, self).default_get(fields_list)
        context = self.env.context
        active_model = context.get('active_model')
        active_ids = context.get('active_ids', [])
        if active_model == 'project.task' and active_ids:
            records = self.env[active_model].browse(active_ids)
            task_types = []
            for record in records:
                project = record.project_id
                if project:
                    task_types.append(set(project.type_ids.ids))
            if task_types:
                common_task_type_ids = list(set.intersection(*task_types))
                defaults['default_stage_ids'] = [(6, 0, common_task_type_ids)]
        return defaults


    @api.depends('project_team_id')
    def _compute_team_member_ids(self):
        for record in self:
            if record.project_team_id:
                record.team_member_ids = record.project_team_id.team_members_ids
            else:
                record.team_member_ids = [(6, 0, [])]


    def add_assignees(self):
        task_ids = self.env.context.get('active_ids', [])
        if not task_ids:
            return
        tasks = self.env['project.task'].browse(task_ids)
        for task in tasks:
            task.write({
                'user_ids': [(4, user.id) for user in self.user_ids],
                'project_team_ids': [(4, self.project_team_id.id)],
                'stage_id': self.stage_id.id,
            })
        return True
