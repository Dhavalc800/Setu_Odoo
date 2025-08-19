from odoo import api, fields, models, api, _


class LeadCallbackInfo(models.Model):
    _name = 'lead.callback.info'
    _description = "Callback Leads Info"
    _order = 'callback_time desc'

    lead_id = fields.Many2one('lead.data.lead', string="Lead", required=True)
    name = fields.Char(related="lead_id.x_name", store=True)
    email = fields.Char(related="lead_id.x_email", store=True)
    phone = fields.Char(related="lead_id.x_phone", store=True)
    callback_time = fields.Datetime(string="Callback Time", required=True)
    lead_list_id1 = fields.Many2one(related="lead_id.lead_list_id", string="Lead List")
    user_id = fields.Many2one('res.users', string="Called By", default=lambda self: self.env.uid)
    call_time = fields.Datetime(string='Call Time', default=fields.Datetime.now)
    disposition_id = fields.Many2one('dispo.list.name', string='Disposition', required=True)
    remark = fields.Text(string="Remark")
    is_fetched_callback = fields.Boolean(
        string="Fetched Callback",
        default=False,
        help="Marked True when lead is fetched and disposition is set"
    )

    campaign_id = fields.Many2one(
        'campaigns.list',
        string="Campaign",
        related='lead_id.campaign_id',
        store=True,
        readonly=True
    )
    lead_list_id = fields.Many2one('lead.list', string="Lead List")

    def action_load_callback_lead(self):
        self.ensure_one()
        
        # Search for the lead by phone number
        lead = self.env['lead.data.lead'].search([
            ('x_phone', '=', self.phone)
        ], limit=1)
        if not lead:
            raise UserError("No lead found with this phone number!")
        
        # Get or create the fetch wizard record
        fetch_wizard = self.env['fetch.lead.user'].search([], order='id desc')
        if fetch_wizard:
            fetch_wizard.lead_id = lead.id