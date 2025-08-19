from odoo import models, fields, api
from odoo.exceptions import UserError

class UpdateLeadListWizard(models.TransientModel):
    _name = 'update.lead.list.wizard'
    _description = 'Update Lead List for Selected Leads'

    lead_list_id = fields.Many2one(
        'lead.list.data', 
        string='Lead List', 
        required=True
    )
    
    lead_ids = fields.Many2many(
        'lead.data.lead', 
        string='Selected Leads',
        default=lambda self: self._get_default_leads()
    )

    def _get_default_leads(self):
        """ Get selected leads from context """
        if self._context.get('active_model') == 'lead.data.lead':
            return [(6, 0, self._context.get('active_ids', []))]
        return False

    def action_update_lead_list(self):
        """ Assign lead list to selected leads """
        self.ensure_one()
        
        if not self.lead_ids:
            raise UserError("No leads selected!")
            
        if not self.lead_list_id:
            raise UserError("Please select a Lead List")
            
        # Update leads in single database operation
        self.lead_ids.write({'lead_list_id': self.lead_list_id.id})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Updated {len(self.lead_ids)} lead(s)',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }