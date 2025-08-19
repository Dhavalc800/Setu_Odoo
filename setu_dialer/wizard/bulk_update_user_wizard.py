from odoo import models, fields, api

class BulkUpdateUserWizard(models.TransientModel):
    _name = 'bulk.update.user.wizard'
    _description = 'Bulk Update Salesperson'

    user_id = fields.Many2one('res.users', string='New Salesperson', required=True)

    def action_update_users(self):
        """ Open wizard with selected assignments """
        return {
            'name': 'Assign Lead to User',
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.update.user.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_assignment_ids': [(6, 0, self.ids)],
                'active_ids': self.ids,
                'active_model': 'bulk.update.user.wizard',
            },
        }