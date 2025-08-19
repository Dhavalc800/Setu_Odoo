from odoo import fields, models, api
from dateutil.relativedelta import relativedelta


class ProjectTask(models.Model):
    _inherit = "project.task"

    operation_activity_ids = fields.One2many(
        "operation.task.activity", "task_id", string="Operation Activity's"
    )
    resubmission_date = fields.Date(string='RESUBMISSION DATE')
    incorporation_date = fields.Date(string="Incorporation Date", tracking=True)
    submission_date = fields.Date(string="Submission Date", tracking=True)
    rm_employee_id = fields.Many2one("hr.employee", string="RM Name", tracking=True)
    rm_remark = fields.Text(string="RM Remark", tracking=True)

    def action_project_task_wizard(self):
        """ Open wizard with selected assignments """
        return {
            'name': 'Update Stage',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.stages',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_assignment_ids': [(6, 0, self.ids)],
                'active_ids': self.ids,
                'active_model': 'project.task.stages',
            },
        }

    def action_pysical_meeting_wizard(self):
        """ Open wizard with selected assignments """
        return {
            'name': 'Assign pysical Meeting to User',
            'type': 'ir.actions.act_window',
            'res_model': 'pysical.meeting.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_assignment_ids': [(6, 0, self.ids)],
                'active_ids': self.ids,
                'active_model': 'pysical.meeting.wizard',
            },
        }

    @api.onchange('incorporation_date')
    def _onchange_incorporation_date(self):
        for task in self:
            if task.incorporation_date and task.sale_line_id.product_id.product_tmpl_id.is_seedfund:
                task.date_deadline = task.incorporation_date + relativedelta(years=2)

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        for task in self:
            if 'incorporation_date' in vals and task.incorporation_date and \
                task.sale_line_id.product_id.product_tmpl_id.is_seedfund:
                task.date_deadline = task.incorporation_date + relativedelta(years=2)
        return res

    @api.model
    def create(self, vals):
        task = super(ProjectTask, self).create(vals)
        if vals.get('incorporation_date') and \
           task.sale_line_id.product_id.product_tmpl_id.is_seedfund:
            task.date_deadline = task.incorporation_date + relativedelta(years=2)
        return task

    # def write(self, vals):
    #     if 'active' in vals:
    #         if vals['active'] is True:
    #             if not self.sale_order_id.agreement_id.stage_id[0].is_active:
    #                 raise UserError("You cannot unarchive the task because the associated agreement stage is not active.")
        
    #     return super(ProjectTask, self).write(vals)