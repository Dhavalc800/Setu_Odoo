from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime

class CampaignsList(models.Model):
    _name = 'campaigns.list'
    _description = "Campaigns List"
    _order = 'create_date desc'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True, tracking=True)
    start_date = fields.Date(string="Start Date", tracking=True)
    end_date = fields.Date(string="End Date", tracking=True)
    disposition_id = fields.Many2one('disposition.list.configuration', string='Disposition List', tracking=True)
    select_method_upd = fields.Selection(
        [("manually", "Manually Select Users"), ("csv", "Add From csv"), ("excel", "Add From Excel")],
        string="Manually Select Users",
        default="manually",
        tracking=True
    )
    user_ids = fields.Many2many('res.users', string="Users", tracking=True)
    cmp_active = fields.Boolean(default=True, tracking=True)

    lead_list_count = fields.Integer(
        string="Lead Lists",
        compute="_compute_lead_list_count",
        tracking=True
    )
    fetch_lead_as_per_disposition = fields.Boolean("Fetch Lead As Per Disposition", tracking=True)
    filter_campaign_id = fields.Many2one('campaigns.list', string="Filter Campaign", tracking=True)
    filter_lead_list_id = fields.Many2many('lead.list.data', string="Filter Lead List", tracking=True)
    filter_disposition_id = fields.Many2many('dispo.list.name', string="Filter Disposition", tracking=True)
    user_count = fields.Integer(string="Campaigns Users", tracking=True)
    used_lead_count = fields.Integer(string="Used Leads", compute="_compute_lead_usage_counts", tracking=True)
    not_used_lead_count = fields.Integer(string="Not Used Leads", compute="_compute_lead_usage_counts", tracking=True)
    total_lead_count = fields.Integer(string="Total Leads", compute="_compute_lead_usage_counts", tracking=True)
    active_user_count = fields.Integer(string="Active Users", compute="_compute_active_user_count", tracking=True)

    def _compute_active_user_count(self):
        Lead = self.env['lead.data.lead']
        for record in self:
            active_users = set()
            if record.user_ids:
                leads = Lead.search([
                    ('campaign_id', '=', record.id),
                    ('is_fetch', '=', True),
                    ('fetch_user_id', 'in', record.user_ids.ids)
                ])
                active_users = set(leads.mapped('fetch_user_id').ids)
            record.active_user_count = len(active_users)

    @api.model
    def create(self, vals):
        record = super(CampaignsList, self).create(vals)
        if vals.get('user_ids'):
            record._reassign_users_to_campaign()
        return record

    def write(self, vals):
        res = super(CampaignsList, self).write(vals)
        if 'user_ids' in vals:
            self._reassign_users_to_campaign()
        return res

    def _reassign_users_to_campaign(self):
        for user in self.user_ids:
            # Search for all other campaigns where this user is present
            other_campaigns = self.search([
                ('id', '!=', self.id),
                ('user_ids', 'in', user.id),
            ])
            for campaign in other_campaigns:
                campaign.user_ids = [(3, user.id)]  # Remove user from other campaign

    def _compute_lead_usage_counts(self):
        for record in self:
            leads = self.env['lead.data.lead'].search([('campaign_id', '=', record.id), ('campaign_id.cmp_active', '!=', False), ('lead_list_id.lead_active', '=', True)])
            record.used_lead_count = len(leads.filtered(lambda l: l.lead_usage_status == 'used'))
            record.not_used_lead_count = len(leads.filtered(lambda l: l.lead_usage_status == 'not_used'))
            record.total_lead_count = len(leads)

    @api.depends('user_ids')
    def _compute_user_count(self):
        for rec in self:
            rec.user_count = len(rec.user_ids)

    def action_view_campaign_users(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Campaign Users',
            'res_model': 'res.users',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.user_ids.ids)],
            'context': dict(self.env.context),
        }

    def action_fetch_per_disposition_leads(self):
        if self.fetch_lead_as_per_disposition:
            lead_histories = self.env['lead.call.history'].search([
                ('campaign_id', '=', self.id),
                ('lead_list_id', 'in', self.filter_lead_list_id.ids),
                ('disposition_id', 'in', self.filter_disposition_id.ids),
            ])

            for history in lead_histories:
                matching_leads = self.env['lead.data.lead'].search([
                    ('x_name', '=', history.lead_id.x_name),
                    ('x_phone', '=', history.lead_id.x_phone),
                ], order='create_date asc')

                for lead in matching_leads:
                    call_histories = self.env['lead.call.history'].search([
                        ('lead_id', '=', lead.id)
                    ], order='call_time desc')

                    if not call_histories:
                        continue

                    latest_dispo = call_histories[0].disposition_id
                    any_positive = any(
                        h.disposition_id.is_intrested or 
                        h.disposition_id.is_callback or 
                        h.disposition_id.is_dnd
                        for h in call_histories
                    )

                    if not latest_dispo.is_intrested and not latest_dispo.is_callback and not latest_dispo.is_dnd and not any_positive:
                        lead.write({
                            'is_fetch': False,
                            'fetch_reset_time': datetime.now(),
                        })

    def _compute_lead_list_count(self):
        for record in self:
            record.lead_list_count = self.env['lead.list.data'].search_count([('campaign_id', '=', record.id)])

    def action_open_lead_lists(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lead Lists',
            'res_model': 'lead.list.data',
            'view_mode': 'tree,form',
            'domain': [('campaign_id', '=', self.id)],
            'context': {'default_campaign_id': self.id},
        }

    def action_clear_users(self):
        for record in self:
            cleared_by = self.env.user.name
            record.user_ids = [(5, 0, 0)]
            record.message_post(
                body=f"<b>Users cleared</b> by <i>{cleared_by}</i>.",
                message_type='comment'
            )

    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for record in self:
            if record.start_date and record.end_date and record.end_date < record.start_date:
                raise ValidationError(_("End Date cannot be earlier than Start Date."))

    def upload_csv(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Upload Users',
            'res_model': 'campaigns.upload.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_campaign_id': self.id
            },
        }
    
    def upload_excel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Upload Users',
            'res_model': 'campaigns.upload.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_campaign_id': self.id
            },
        }