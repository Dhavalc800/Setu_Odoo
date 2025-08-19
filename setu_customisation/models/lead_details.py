from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class LeadDetails(models.Model):
    _inherit = 'lead.details'
    _order = 'create_date desc'

    sequence_id = fields.Integer(string='Sequence', index=True, readonly=True, tracking=True)
    lead_partner_id = fields.Many2one('res.partner', string="Lead Name", tracking=True)
    lead_source = fields.Char(string="Source", tracking=True)
    company_type = fields.Char(string="Company Type", tracking=True)
    lead_slab = fields.Char(string="Slab", tracking=True)
    crm_phone = fields.Char(string="Crm Phone")
    lead_disposition = fields.Char(string="Disposition", tracking=True)
    lead_service = fields.Char(string="Lead Service", tracking=True)
    campaign_name = fields.Char(string="Campaign Name", tracking=True)
    crm_lead_id = fields.Many2one('crm.lead', tracking=True)
    assign_user_id = fields.Many2one('res.users', string="Added By", tracking=True)
    formatted_phone_number = fields.Char(string="Phone Number", compute='_compute_formatted_phone_number', store=False)
    state = fields.Selection([
        ('not_created', 'Not Created'),
        ('created', 'Created'),
    ], string='Lead State', default='not_created', tracking=True)


    @api.depends('crm_lead_id')
    def _compute_formatted_phone_number(self):
        for record in self:
            if record.crm_lead_id:
                record.crm_phone = record.phone_number
                record.formatted_phone_number = record.phone_number
            else:
                if record.phone_number:
                    record.crm_phone = record.phone_number
                    record.formatted_phone_number = f"{record.phone_number[:2]}XXXXXX{record.phone_number[-2:]}"
                else:
                    record.formatted_phone_number = ''

    @api.model
    def create(self, vals):
        if 'lead_id' not in vals or not vals['lead_id']:
            vals['lead_id'] = self.env['ir.sequence'].next_by_code('lead.details')

        vals['sequence_id'] = self.env['ir.sequence'].next_by_code('lead.details.sequence')

        if not vals.get('lead_name'):
            print("\n\n\nWarning: lead_name is missing in vals:", vals)
        return super(LeadDetails, self).create(vals)

    def action_lead(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Lead',
            'res_model': 'lead.details.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.lead_partner_id.id,
                'default_email': self.lead_email,
                'default_phone': self.formatted_phone_number,
                'default_assign_user_id': self.assign_user_id.id,
                'default_crm_phone': self.crm_phone,
            },
        }
    
    def get_leads(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Leads',
            'res_model': 'crm.lead',
            'res_id': self.crm_lead_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def update_crm_lead_phone_numbers(self):
        """Automatically update phone numbers in crm.lead from lead.details"""

        leads = self.env['lead.details'].search([('crm_lead_id', '!=', False)])

        for lead in leads:
            if lead.crm_phone and lead.crm_lead_id:
                lead.crm_lead_id.phone = lead.crm_phone
                print("\n\n\nLeadddddddddd",lead)