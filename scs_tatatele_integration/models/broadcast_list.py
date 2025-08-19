from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BroadcastList(models.Model):
    _name = 'broadcast.list'
    _description = "Broadcast List"

    list_id = fields.Char(required=True)
    name = fields.Char(string="Name")
    lead_details_ids = fields.One2many('lead.details', 'broadcast_list_id', "Leads")
    broadcastid = fields.Integer(string="Broadcast ID")

    def fetch_list_lead_detail(self):
        TataControl = self.env['tatatele.connector']
        user = self.env.user
        for rec in self:
            if not (user.tata_email and user.tata_password and user.access_token):
                raise UserError(
                    _("No Tata TeleService Configuration Added. Please Check !")
                )
            list_url = self.env.user.host + "v1/broadcast/leads/%s" % rec.list_id
            get_lists_lead = TataControl.call(user, request_url=list_url, verb="GET")
            if get_lists_lead.status_code == 401:
                self.env.user.generate_access_token()

            if isinstance(get_lists_lead.json(), dict):
                continue

            if get_lists_lead.status_code == 200:
                if not isinstance(get_lists_lead.json(), dict):
                    for data in get_lists_lead.json():
                        exist_lead_id = self.env["lead.details"].sudo().search([
                            ('lead_id', '=', data.get('id'))
                        ])
                        if data.get('lead_picked') != 0 and not exist_lead_id:
                            lead_vals = {
                                "lead_id": data.get("id"),
                                "listId": data.get("list_id"),
                                'broadcast_list_id': self.env['broadcast.list'].search([('list_id', '=', rec.list_id)], limit=1).id,
                                "phone_number": data.get("field_0"),
                                "lead_name": data.get("field_1"),
                                "lead_email": data.get("field_2"),
                                "lead_address": data.get("field_3"),
                                "lead_company_name": data.get("field_4"),
                                "list_name": data.get("list_name"),
                                "time_group": data.get("time_group"),
                                "added_by": data.get("added_by"),
                                "lead_picked": data.get("lead_picked"),
                            }
                            leads = self.env["lead.details"].create(lead_vals)
                            print("leads-----------", leads)

    def action_leads_details(self):
        action = {
            'res_model': 'lead.details',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'name': self.name,
            'domain': [('listId', '=', self.list_id)],
            'context':{'create': 0, 'edit':0}
        }
        return action


class LeadDetails(models.Model):
    _name = 'lead.details'
    _description = "Lead Details"
    _rec_name = "lead_id"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    lead_id = fields.Char("Lead")
    listId = fields.Char("List")
    broadcast_list_id = fields.Many2one("broadcast.list", "List")
    phone_number = fields.Char("Phone number")
    lead_name = fields.Char("Lead name")
    lead_email = fields.Char("Lead Email")
    lead_address = fields.Char("Lead Address")
    lead_company_name = fields.Char("Lead Company")
    list_name = fields.Char("List name")
    time_group = fields.Char("Time Group")
    added_by = fields.Char("Added By")
    lead_picked = fields.Char("Lead picked")


class TatateleDepartment(models.Model):
    _name = 'tatatele.department'
    _description = 'Tata Tele Department'

    name = fields.Char("Department Name")
    description = fields.Char("Description")
    departmentid = fields.Char("Department ID")
    ring_strategy = fields.Selection([('simultaneously', "Simultaneously"), ('order_by', 'Order by'),
                                      ('random', 'Random'), ('round_robin', 'Round Robin'),
                                      ('longest_wait_time', 'Longest Wait time')], "Ring Strategy")
    agent_count = fields.Char("Agents Count")
    calls_answered = fields.Char("Calls Answered")
    calls_missed = fields.Char("Calls Missed")
    use_as_queue = fields.Boolean("Use as Queue")
    queue_timeout = fields.Char("Queue Timeout")
    agent_ids = fields.One2many("res.users", 'tatatele_department_id', "Agents")
