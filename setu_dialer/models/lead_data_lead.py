from odoo import api, fields, models, _


class LeadDataLead(models.Model):
    _name = 'lead.data.lead'
    _description = "Lead Data Lead"
    _rec_name = 'x_name'
    _order = 'create_date desc'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    x_name = fields.Char("Name", tracking=True)
    x_email = fields.Char("Email", tracking=True)
    x_phone = fields.Char("Phone", tracking=True)
    lead_list_id = fields.Many2one('lead.list.data', string="Lead List", tracking=True)
    is_fetch = fields.Boolean(string="Is Fetched", default=False, tracking=True)
    fetch_reset_time = fields.Datetime(string="Fetch Reset Time", tracking=True)
    dynamic_field_values = fields.Text(string="Lead Data", readonly=True, tracking=True)
    dynamic_summary = fields.Text("Dynamic Summary", tracking=True)
    campaign_id = fields.Many2one(
        'campaigns.list',
        string="Campaign",
        related='lead_list_id.campaign_id',
        store=True,
        readonly=True,
        tracking=True
    )
    fetch_user_id = fields.Many2one('res.users', string="Fetched By", tracking=True)
    fetch_date = fields.Datetime(string="Fetched At", tracking=True)
    lead_usage_status = fields.Selection([
            ('used', 'Used'),
            ('not_used', 'Not Used')
        ], string="Lead Usage Status", compute="_compute_lead_usage_status", store=True, tracking=True)

    @api.depends('is_fetch')
    def _compute_lead_usage_status(self):
        for rec in self:
            if rec.is_fetch:
                rec.lead_usage_status = 'used'
            else:
                rec.lead_usage_status = 'not_used'


    @api.model
    def create(self, vals):
        record = super().create(vals)

        model_fields = self.env['ir.model.fields'].sudo().search([
            ('model', '=', 'lead.data.lead'),
            ('name', 'like', 'x_')
        ])
        label_map = {f.name: f.field_description for f in model_fields}

        dynamic_data = ""
        for field in record._fields:
            if field.startswith('x_') and hasattr(record, field):
                value = getattr(record, field, '')
                if value:
                    label = label_map.get(field, field)
                    dynamic_data += f"{label}: {value}\n"

        record.dynamic_field_values = dynamic_data
        
        return record

    def action_view_lead_list(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Lead List'),
            'view_mode': 'form',
            'res_model': 'lead.list.data',
            'res_id': self.lead_list_id.id,
            'target': 'current',
        }
    
    def action_open_assign_wizard(self):
        """ Open wizard with selected leads """
        return {
            'name': 'Assign Lead List',
            'type': 'ir.actions.act_window',
            'res_model': 'update.lead.list.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_ids': [(6, 0, self.ids)],
                'active_ids': self.ids,
                'active_model': 'lead.data.lead'
            },
        }