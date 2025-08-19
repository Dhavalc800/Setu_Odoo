from odoo import api, fields, models, _
from datetime import datetime, time
from datetime import date



class LeadListData(models.Model):
    _name = 'lead.list.data'
    _description = "Lead List Data"
    _order = "create_date desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Lead List Name", required=True, tracking=True)
    list_description = fields.Text(string="Lead List Description", tracking=True)
    list_date = fields.Date(string="Lead List Date", required=True, tracking=True, default=lambda self: date.today())
    report_column_ids = fields.Many2many(
        'report.column',
        'wizard_report_column_rel',
        'wizard_id',
        'column_id',
        string='Report Columns',
        default=lambda self: self._default_report_columns(),
        tracking=True
    )
    campaign_id = fields.Many2one('campaigns.list', string="Campaign", tracking=True)
    lead_active = fields.Boolean("Lead Active", default=True, tracking=True)
    lead_data_ids = fields.One2many(
        'lead.data.lead', 'lead_list_id', string="Leads", tracking=True
    )
    used_lead_count = fields.Integer(string="Used Leads", compute="_compute_lead_usage_counts", tracking=True)
    not_used_lead_count = fields.Integer(string="Not Used Leads", compute="_compute_lead_usage_counts", tracking=True)
    total_lead_count = fields.Integer(string="Total Leads", compute="_compute_lead_usage_counts", tracking=True)

    @api.depends('lead_data_ids.lead_usage_status', 'lead_active')
    def _compute_lead_usage_counts(self):
        for record in self:
            if record.lead_active:
                leads = record.lead_data_ids
                record.used_lead_count = len(leads.filtered(lambda l: l.lead_usage_status == 'used'))
                record.not_used_lead_count = len(leads.filtered(lambda l: l.lead_usage_status == 'not_used'))
                record.total_lead_count = len(leads)
            else:
                # Ensure all fields are still assigned even when inactive
                record.used_lead_count = 0
                record.not_used_lead_count = 0
                record.total_lead_count = 0

    # @api.depends('lead_data_ids.lead_usage_status')
    # def _compute_lead_usage_counts(self):
    #     for record in self:
    #         if not record.lead_active:
    #             leads = record.lead_data_ids
    #             record.used_lead_count = len(leads.filtered(lambda l: l.lead_usage_status == 'used'))
    #             record.not_used_lead_count = len(leads.filtered(lambda l: l.lead_usage_status == 'not_used'))
    #             record.total_lead_count = len(leads)

    def action_open_leads(self):
        self.ensure_one()
        return {
            'name': _('Leads'),
            'type': 'ir.actions.act_window',
            'res_model': 'lead.data.lead',
            'view_mode': 'tree,form',
            'domain': [('lead_list_id', '=', self.id)],
            'context': {
                'default_lead_list_id': self.id
            }
        }

    @api.model
    def cron_deactivate_leads(self):
        """Deactivate all lead lists at 10:00 PM daily"""
        records = self.search([('lead_active', '=', True)])
        records.write({'lead_active': False})

    @api.model
    def _default_report_columns(self):
        """Ensure default fields (Name, Email, Phone) exist and return them"""
        default_names = ['name', 'email', 'phone']
        default_columns = []
        for field_name in default_names:
            column = self.env['report.column'].sudo().search([('name', '=', field_name)], limit=1)
            
            if column:
                default_columns.append(column.id)
        return [(6, 0, default_columns)]

    def action_open_export_wizard(self):
        """Open the export wizard"""
        self.ensure_one()
        return {
            'name': _('Import Lead List'),
            'type': 'ir.actions.act_window',
            'res_model': 'lead.data.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_list_id': self.id,
            }
        }
    
    def action_download_csv(self):
        self.ensure_one()
        download_url = f"/lead_list/{self.id}/download_csv"
        
        return {
            'type': 'ir.actions.act_url',
            'url': download_url,
            'target': 'new'
        }

# class LeadDataLead(models.Model):
#     _name = 'lead.data.lead'
#     _description = "Lead Data Lead"
#     _rec_name = 'x_name'

#     x_name = fields.Char("Name")
#     x_email = fields.Char("Email")
#     x_phone = fields.Char("Phone")
#     lead_list_id = fields.Many2one('lead.list.data', string="Lead List")
    # parent_id = fields.Many2one('lead.data.lead', string="Parent Lead")
    # child_ids = fields.One2many('lead.data.lead', 'parent_id', string="Sub Leads")

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

    #     if view_type == 'form':
    #         doc = etree.XML(res['arch'])

    #         # Insert dynamic fields into a new notebook page
    #         sheet = doc.xpath("//sheet")
    #         if sheet:
    #             notebook = sheet[0].find('notebook')
    #             if notebook is None:
    #                 notebook = etree.SubElement(sheet[0], 'notebook')

    #             page = etree.SubElement(notebook, 'page', string="Dynamic Fields")
    #             group = etree.SubElement(page, 'group')

    #             # Add all fields starting with x_ that are not already in the view
    #             static_fields = {'x_name', 'x_email', 'x_phone'}
    #             for field_name in self._fields:
    #                 if field_name.startswith('x_') and field_name not in static_fields:
    #                     etree.SubElement(group, 'field', name=field_name)

    #         res['arch'] = etree.tostring(doc, encoding='unicode')
    #     return res