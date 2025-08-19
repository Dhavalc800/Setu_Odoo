import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import datetime
import json


class CallRecordDetails(models.Model):
    _name = "call.record.details"
    _description = "Call Record Details"
    _rec_name = "client_number"

    name = fields.Char(
        'Name', copy=False, required=True, readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('call.detail'))
    call_record_id = fields.Char("Call Record Id")
    call_id = fields.Char("Call Id")
    call_direction = fields.Selection(
        [("inbound", "Inbound"), ("outbound", "Outbound")], string="Call Direction"
    )
    description = fields.Char("Description")
    detailed_description = fields.Char("Detailed Description")
    call_status = fields.Selection(
        [("missed", "Missed"), ("answered", "Answered")], string="Call Status"
    )
    recording_url = fields.Char("Recording Url")
    service = fields.Char("Service")
    call_start_date_time = fields.Datetime("Call Start Date Time")
    call_end_date_time = fields.Datetime("Call Ent Date Time")
    broadcast_id = fields.Many2one("broadcast.list", "Broadcast")
    call_duration = fields.Float("Call Duration")
    answered_seconds = fields.Float("Answered Seconds")
    minutes_consumed = fields.Float("Minutes Consumeds")
    agent_number = fields.Char("Agent Number")
    agent_number_with_prefix = fields.Char("Agent Number With Prefix")
    agent_name = fields.Char("Agent Name")
    client_number = fields.Char("Client Number")
    caller_id_num = fields.Char("caller Id Number")
    hangup_cause = fields.Char("Hangup Cause")
    notes = fields.Text("Notes")
    missed_agents_number = fields.Char("Missed Agents Number")
    missed_agents_name = fields.Char("Missed Agents Name")
    call_flow_type = fields.Char("Call Flow Type")
    call_flow_name = fields.Char("Call Flow Name")
    call_flow_num = fields.Char("Call Flow Number")
    call_flow_dialst = fields.Char("Call Flow Dialst")
    call_flow_time = fields.Char("Call Flow Time")
    is_call_detail_import = fields.Boolean("Is Imported")
    disposition_name = fields.Char("Disposition")
    is_lead_created = fields.Boolean("Is Lead Created")
    lead_id = fields.Many2one('crm.lead', "Lead")
    user_id = fields.Many2one('res.users', "User")
    leadid = fields.Char('LeadID')

    def create_lead(self):
        crm_obj = self.env['crm.lead']
        for rec in self:
            if rec.is_lead_created:
                raise ValidationError(_("These Call Details (%s) have already been converted into Lead\n Please "
                                        "don't select these call disposition") % (rec.name))
            vals = {}
            client_name = self.env['lead.details'].search([('lead_id', '=', self.leadid)], limit=1).lead_name
            vals.update({
                'name': client_name or rec.client_number,
                'client_number': rec.client_number,
                'user_id': rec.user_id and rec.user_id.id or False,
                'call_details': rec.id
            })
            lead_id = crm_obj.create(vals)
            if lead_id:
                rec.is_lead_created = True
                rec.lead_id = lead_id.id

    def _cron_call_recordings(self):
        list_call_details = []
        call_url = "https://api-smartflo.tatateleservices.com/v1/call/records?limit=300?from_date={}&to_date={}".format(
            fields.Datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
            (fields.Datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        )
        admin_user = self.env['res.users'].search([('is_tatatele_admin', '=', True)], limit=1)
        if not admin_user:
            raise ValidationError(_("Please Configure Admin user"))
        if admin_user:
            if not admin_user.access_token:
                raise ValidationError(_("Please Generate Access token for Admin User"))
            if not (admin_user.tata_email or admin_user.tata_password):
                raise ValidationError(_("Please Enter Admin User's Tata Tele Credentials"))
        auth_token = ("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzMDM5OTQiLCJpc3MiOiJodHRwczovL2Nsb3VkcGhvbmUudGF"
                      "0YXRlbGVzZXJ2aWNlcy5jb20vdG9rZW4vZ2VuZXJhdGUiLCJpYXQiOjE3MDA1Njg0NzAsImV4cCI6MjAwMDU2ODQ3MCwibm"
                      "JmIjoxNzAwNTY4NDcwLCJqdGkiOiJjUkV2Ylo2TW9vY3ZvQzlQIn0.1vXndqZVbTZrlgH21SsgBi-wNevbfNtlb-exUMpllBI")
        header = {
            "accept": "application/json",
            "Authorization": 'Bearer %s' % admin_user.access_token,
        }
        get_call_record_details = requests.request(headers=header, url=call_url, method="GET")
        json_to_dict = json.loads(get_call_record_details.text)
        if isinstance(json_to_dict, dict) and json_to_dict.get('success') == False:
            header = {
                "accept": "application/json",
                "Authorization": 'Bearer %s' % auth_token,
            }
            get_call_record_details = requests.request(headers=header, url=call_url, method="GET")
        if isinstance(json_to_dict, dict):
            list_call_details.append(get_call_record_details.json())
            call_rec = {}
            if isinstance(list_call_details[0].get("results"), list):
                for call_detail in list_call_details[0].get("results"):
                    existed_call_id = self.search(
                        [
                            ("is_call_detail_import", "=", False),
                            ("call_record_id", "=", call_detail.get("id")),
                        ]
                    )
                    if not existed_call_id:
                        call_rec.update({
                            "is_call_detail_import": True,
                            "call_record_id": call_detail.get("id", False),
                            "call_id": call_detail.get("call_id", False),
                            "call_direction": call_detail.get("direction", False),
                            "description": call_detail.get("description", False),
                            "detailed_description": call_detail.get(
                                "detailed_description", False
                            ),
                            "call_status": call_detail.get("status", False),
                            # "recording_url": call_detail.get("recording_url") and shortner.tinyurl.short(call_detail.get("recording_url", None)) or False,
                            "recording_url": call_detail.get("recording_url", None),
                            "service": call_detail.get("service", False),
                            "call_start_date_time": call_detail.get("date", False),
                            "call_end_date_time": call_detail.get("end_stamp", False),
                            "broadcast_id": self.env['broadcast.list'].search(
                                [('broadcastid', '=', call_detail.get("broadcast_id", False))], limit=1).id,
                            "call_duration": call_detail.get("call_duration", False),
                            "answered_seconds": call_detail.get("answered_seconds", False),
                            "minutes_consumed": call_detail.get("minutes_consumed", False),
                            "agent_number": call_detail.get("agent_number", False),
                            "agent_number_with_prefix": call_detail.get(
                                "agent_number_with_prefix", False
                            ),
                            "agent_name": call_detail.get("agent_name", False),
                            "client_number": call_detail.get("client_number", False),
                            "caller_id_num": call_detail.get("did_number", False)
                                             or call_detail.get("caller_id_num", False),
                            "hangup_cause": call_detail.get("hangup_cause", False),
                            "notes": call_detail.get("notes", False),
                            "missed_agents_number": call_detail.get("missed_agents")
                                                    and call_detail.get("missed_agents")[0].get("number"),
                            "missed_agents_name": call_detail.get("missed_agents")
                                                  and call_detail.get("missed_agents")[0].get("name"),
                            "disposition_name": call_detail.get('dialer_call_details') and call_detail.get(
                                'dialer_call_details').get('disposition_name'),
                            "leadid": call_detail.get('lead_id') or False,
                            # "user_id": self.env['res.users'].search([('agent_id', '=', call_detail.get("call_flow")
                            # and call_detail.get("call_flow")[2] and call_detail.get("call_flow")[2].get("id"))], limit=1).id or False
                            # "call_flow_type": call_detail.get("call_flow")
                            # and call_detail.get("call_flow")[2].get("type"),
                            # "call_flow_name": call_detail.get("call_flow")
                            # and call_detail.get("call_flow")[2].get("name"),
                            # "call_flow_num": call_detail.get("call_flow")
                            # and call_detail.get("call_flow")[2].get("num"),
                            # "call_flow_dialst": call_detail.get("call_flow")
                            # and call_detail.get("call_flow")[2].get("dialst"),
                            # "call_flow_time": call_detail.get("call_flow")
                            # and call_detail.get("call_flow")[2].get("time"),
                        })
                    call_details = self.create(call_rec)
                    print("call_details-------", call_details)


