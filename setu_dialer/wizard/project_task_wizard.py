from odoo import models, fields, api

class ProjectTaskStages(models.TransientModel):
    _name = 'project.task.stages'
    _description = 'Project Task Stages'

    stage_id = fields.Many2one("project.task.type", string="Stage")

    def action_apply_stages(self):
        active_ids = self.env.context.get('active_ids', [])
        tasks = self.env['project.task'].browse(active_ids)
        target_stage = self.stage_id

        for task in tasks:
            if target_stage.project_ids and task.project_id in target_stage.project_ids:
                task.stage_id = target_stage
            else:
                continue