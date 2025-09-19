from odoo import api, fields, models, _


class DispoListName(models.Model):
    _name = 'dispo.list.name'
    _description = "Dispo List Name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Dispo Name", tracking=True)
    is_dnd = fields.Boolean(string="Is DND", tracking=True)
    is_intrested = fields.Boolean(string="Is Intrested", tracking=True)
    is_callback = fields.Boolean(string="Is Call Back", tracking=True)
    is_expo = fields.Boolean(string="Is Physical", tracking=True)
    show_in_callback = fields.Boolean(
        string="Show in Callback List",
        default=True,
        tracking=True,
        help="If checked, leads with this disposition will appear in callback list"
    )
    is_show = fields.Boolean(string="Is Show")
    is_opportunity = fields.Boolean(string="Is Opportunity")

class DNDLead(models.Model):
    _name = 'lead.dnd'
    _description = 'DND Leads'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char("Name", tracking=True)
    email = fields.Char("Email", tracking=True)
    phone = fields.Char("Phone", required=True, tracking=True, index=True, unique=True)

class LeadCallbackHistory(models.Model):
    _name = 'lead.callback.history'
    _description = "Lead Callback History"

    # fetch_wizard_id = fields.Many2one('fetch.lead.user')
    lead_id = fields.Many2one('lead.data.lead', string="Lead")
    user_id = fields.Many2one('res.users', string="User")
    callback_time = fields.Datetime(string="Scheduled Callback Time")
