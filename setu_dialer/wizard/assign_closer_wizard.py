# models/assign_to_closer_wizard.py

from odoo import models, fields, api

class AssignCloserWizard(models.TransientModel):
    _name = 'assign.closer.wizard'
    _description = 'Assign Lead To Closer'

    closer_id = fields.Many2one('closer.name', string='Closer', required=True)
    assignment_ids = fields.Many2many('branch.manager.assignment', string='Assignments')

    def action_assign(self):
        for rec in self.assignment_ids:
            self.env['lead.closer.calling'].sudo().create({
                'lead_id': rec.lead_id.id,
                'user_id': self.env.user.id,
                'employee_id': self.closer_id.id,
                'closer_user_id': self.closer_id.user_id.id,
                'dynamic_summary' : rec.lead_id.dynamic_field_values,
                'source': rec.source,
                'phone': rec.phone,
                'bdm_id': rec.branch_manager_id.id,
            })
            rec.closer_id = self.closer_id.id
        return {'type': 'ir.actions.act_window_close'}
