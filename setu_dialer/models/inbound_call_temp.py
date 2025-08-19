from odoo import models, fields

class InboundCallTemp(models.TransientModel):
    _name = 'inbound.call.temp'

    lead_id = fields.Many2one('lead.data.lead', string="Lead")
    phone = fields.Char(string="Phone")
    caller_number = fields.Char(string="Caller Number")
    call_type = fields.Selection([
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound')
    ], string="Call Type")
    recording = fields.Char(string="Recording")
    lead_fetch_id = fields.Many2one('fetch.lead.user', string="Lead Fetch")


    # def action_use_inbound_call(self):
    #     self.ensure_one()
    #     wizard = self.lead_fetch_id

    #     # Attempt to find lead with this phone number
    #     lead = self.env['lead.data.lead'].search([('x_phone', 'ilike', self.phone)], limit=1)
    #     if lead:
    #         wizard.lead_id = lead.id
    #         wizard.phone_link_html = f'<a href="tel:{lead.x_phone}">{lead.x_phone}</a>'
    #         wizard.dynamic_field_values = lead.dynamic_field_values

    def action_use_inbound_call(self):
        self.ensure_one()
        wizard = self.lead_fetch_id

        lead = self.env['lead.data.lead'].search([('x_phone', 'ilike', self.phone)], limit=1)
        if lead:
            wizard.lead_id = lead.id
            wizard.phone_link_html = f'<a href="tel:{lead.x_phone}">{lead.x_phone}</a>'
            wizard.dynamic_field_values = lead.dynamic_field_values

            # 💡 Refresh inbound call list by clearing and reloading
            wizard.inbound_call_ids = [(5, 0, 0)] + wizard._get_inbound_calls()
