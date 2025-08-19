from odoo import models, fields, api

class LeadCallHistory(models.Model):
    _name = 'lead.call.history'
    _description = 'Lead Call History'
    _order = 'call_time desc'
    _rec_name = 'lead_id'

    lead_id = fields.Many2one('lead.data.lead', string='Lead', required=True)
    user_id = fields.Many2one('res.users', string='Called By', default=lambda self: self.env.user)
    campaign_id = fields.Many2one('campaigns.list', string='Campaign')
    lead_list_id = fields.Many2one('lead.list.data', string='Lead List')
    phone = fields.Char(string='Phone')
    opportunity_name = fields.Char(string="Opportunity Name")
    expected_revenue = fields.Char(string="expected_revenue")
    disposition_id = fields.Many2one('dispo.list.name', string='Disposition', required=True)
    call_time = fields.Datetime(string='Call Time', default=fields.Datetime.now)
    remark = fields.Text(string="Remark")
    is_interested = fields.Boolean(string="Is Interested", compute="_compute_is_interested")

    @api.depends('disposition_id')
    def _compute_is_interested(self):
        for rec in self:
            rec.is_interested = rec.disposition_id.is_intrested
            print("\n\n\nReccccccccccccc",rec.is_interested)
    # @api.model
    # def create(self, vals):
    #     record = super(LeadCallHistory, self).create(vals)

    #     # Also create in merged model
    #     self.env['lead.call.merged'].create({
    #         'lead_id': record.lead_id.id,
    #         'user_id': record.user_id.id,
    #         'campaign_id': record.campaign_id.id,
    #         'lead_list_id': record.lead_list_id.id,
    #         'phone': record.phone,
    #         'call_time': record.call_time,
    #         'disposition_id': record.disposition_id.id,
    #         'remark': record.remark,
    #         'source_model': 'call_history'
    #     })

    #     return record