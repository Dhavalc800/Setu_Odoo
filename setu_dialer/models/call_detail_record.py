from odoo import models, fields

class CallDetailRecord(models.Model):
    _name = 'call.detail.record'
    _description = 'Call Detail Record'
    _rec_name = 'client_name'

    user_id = fields.Many2one('res.users', string='User', readonly=True, default=lambda self: self.env.user)
    client_name = fields.Char(readonly=True)
    lead_id = fields.Many2one('lead.data.lead', string="Lead", readonly=True)
    campaign_id = fields.Many2one('campaigns.list', string='Campaign')
    lead_list_id = fields.Many2one('lead.list.data', string='Lead List')
    disposition_id = fields.Many2one('dispo.list.name', tracking=True, string="Select Disposition")
    client_correlation_id = fields.Char(string="Call ID")
    call_datetime = fields.Datetime(string="Call Time")
    opportunity_name = fields.Char(string="Opportunity Name", tracking=True)
    expected_revenue = fields.Float(string="Expected Revenue", tracking=True)
    remark = fields.Text(string="Remark", tracking=True)
    caller_number = fields.Char(readonly=True)
    destination_number = fields.Char(readonly=True)
    overall_call_status = fields.Char(readonly=True)
    caller_operator_name = fields.Char(readonly=True)
    destination_operator_name = fields.Char(readonly=True)
    call_type = fields.Char(readonly=True)
    caller_circle = fields.Char(readonly=True)
    destination_circle = fields.Char(readonly=True)
    call_duration = fields.Char(readonly=True)
    conversation_duration = fields.Char(readonly=True)
    call_date = fields.Char(readonly=True)
    caller_status = fields.Char(readonly=True)
    destination_status = fields.Char(readonly=True)
    hangup_cause = fields.Char(readonly=True)
    recording = fields.Char("Recording Path", readonly=True)
