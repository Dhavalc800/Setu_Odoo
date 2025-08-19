from odoo import fields, models


class StateHistory(models.Model):
    _name = 'state.history'
    _description = 'State History'

    order_id = fields.Many2one('sale.order', string='Order')
    duration = fields.Float(string='Duration', compute="compute_duration")
    state = fields.Char(string="State")
    user = fields.Many2one('res.users', string='User')
    current_state = fields.Boolean(string="Current State")
    substate_id = fields.Many2one(
        "base.substate",
        string="Sub State")
    project_task_id = fields.Many2one('project.task', string="Tasks")

    def compute_duration(self):
        for rec in self:
            if rec.create_date:
                if rec.current_state:
                    rec.duration = (fields.Datetime.now() - rec.create_date).total_seconds() / 60
                else:
                    rec.duration = (rec.write_date - rec.create_date).total_seconds() / 60
            else:
                rec.duration = 0
