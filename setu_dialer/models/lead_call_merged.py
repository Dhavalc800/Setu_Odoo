from odoo import fields, models, _, api


class LeadCallMerged(models.Model):
    _name = 'lead.call.merged'
    _description = 'Merged Call History and Callback Info'
    _order = 'call_time desc'
    _rec_name = 'lead_id'

    lead_id = fields.Many2one('lead.data.lead', string="Lead")
    user_id = fields.Many2one('res.users', string="Called By")
    campaign_id = fields.Many2one('campaigns.list', string="Campaign")
    lead_list_id = fields.Many2one('lead.list', string="Lead List")
    phone = fields.Char(string="Phone")
    call_time = fields.Datetime(string="Call Time")
    disposition_id = fields.Many2one('dispo.list.name', string="Disposition")
    remark = fields.Text(string="Remark")
    opportunity_name = fields.Char(string="Opportunity Name")
    expected_revenue = fields.Char(string="expected_revenue")
    source_model = fields.Selection([
            ('call_history', 'Call History'),
            ('callback_info', 'Callback Info')
        ], string="Source", readonly=True)

    # Additional fields from external call details
    client_name = fields.Char(string="Client Name")
    caller_number = fields.Char(string="Caller Number")
    destination_number = fields.Char(string="Destination Number")
    call_datetime = fields.Datetime(string='Call Date/Time')
    client_correlation_id = fields.Char(string="Call ID")
    overall_call_status = fields.Char(string="Overall Call Status")
    caller_operator_name = fields.Char(string="Caller Operator Name")
    destination_operator_name = fields.Char(string="Destination Operator Name")
    call_type = fields.Char(string="Call Type")
    caller_circle = fields.Char(string="Caller Circle")
    destination_circle = fields.Char(string="Destination Circle")
    call_duration = fields.Char(string="Call Duration")
    conversation_duration = fields.Char(string="Conversation Duration")
    call_date = fields.Date(string="Call Date")
    caller_status = fields.Char(string="Caller Status")
    destination_status = fields.Char(string="Destination Status")
    hangup_cause = fields.Char(string="Hangup Cause")
    recording = fields.Char(string="Recording Path")
    is_interested = fields.Boolean(string="Is Interested", compute="_compute_is_interested")

    @api.depends('disposition_id')
    def _compute_is_interested(self):
        for rec in self:
            rec.is_interested = rec.disposition_id.is_intrested
