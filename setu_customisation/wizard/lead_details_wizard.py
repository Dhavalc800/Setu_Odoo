from odoo import models, fields, api

class LeadDetailsWizard(models.TransientModel):
    _name = 'lead.details.wizard'
    _description = 'Create Lead Wizard'

    name = fields.Char(string='Lead Opportunity', required=True)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    crm_phone = fields.Char(string="Crm Phone")
    partner_id = fields.Many2one('res.partner', string="Customer")
    assign_user_id = fields.Many2one('res.users', string='Assign By')
    expected_revenue = fields.Monetary(string="Expected Revenue", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    
    def create_lead(self):
        # Create a new crm.lead record
        user = self.env['res.users'].search([('id', '=', self.assign_user_id.id)])
        
        lead_data = {
            'name': self.name,
            'email_from': self.email,
            'phone': self.crm_phone,
            'expected_revenue': self.expected_revenue,
            'user_id': user.id if user else self.env.user.id,
        }
        new_lead = self.env['crm.lead'].create(lead_data)

        # Update the lead.details record to store the created CRM lead reference
        active_id = self.env.context.get('active_id')
        if active_id:
            lead_details = self.env['lead.details'].browse(active_id)
            lead_details.crm_lead_id = new_lead.id
            lead_details.state = 'created'
