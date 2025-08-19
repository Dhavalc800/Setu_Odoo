from odoo import _, api, fields, models
import ast
import json
import requests
from odoo.exceptions import UserError
from datetime import timedelta
import pyshorteners
from dateutil import parser
import pytz
import datetime
import logging
_logger = logging.getLogger(__name__)



class FetchLead(models.TransientModel):
    _name = "fetch.lead"
    _description = "Fetch Lead"

    def get_campaign(self):
        TataControl = self.env['tatatele.connector']
        campaign_obj = self.env['dialer.campaign']
        campaign_details_obj = self.env['campaign.details']
        user = self.env.user
        camp_details_ids = campaign_obj.search([])
        if not camp_details_ids:
            campaign_url = user.host + "v1/dialer/campaign"
            campaign_list = TataControl.call(user, request_url=campaign_url, verb="GET")
            if campaign_list.status_code == 200:
                campaign_details = campaign_list.json()
                campaign_list_vals = [
                    {"campaign_id": campaign.get("id"), 'name': campaign.get('name')} for campaign in campaign_details.get('data')
                ]
                new_campaign_list_id = []
                for new_campaign_id in campaign_list_vals:
                    campaign_list_id = campaign_obj.search([("campaign_id", "!=", new_campaign_id.get("campaign_id"))])
                    if not campaign_list_id:
                        new_campaign_list_id.append({"campaign_id": new_campaign_id.get("campaign_id"), 'name': new_campaign_id.get('name')})
                if new_campaign_list_id:
                        campaign_obj.create(new_campaign_list_id)
        else:
            camp_vals = {}
            for camp in camp_details_ids:
                camp_url = user.host + "v1/dialer/campaign/%s" % camp.campaign_id
                camp_details = TataControl.call(user, request_url=camp_url, verb="GET")
                if camp_details.status_code == 200:
                    campaign_details = camp_details.json()
                    data = campaign_details.get('data')
                    camp_vals.update({
                        'campaignId': data.get('id'),
                        'name': data.get('name'),
                        'description': data.get('description'),
                    })
                    camp_rec = campaign_details_obj.create(camp_vals)
                    for agent in data.get('agent'):
                        if not self.env['res.users'].search([('login', '=', agent.get('name'))]):
                            camp_rec.user_ids = [(0, 0, {
                                    'agent_id': agent.get('id'),
                                    'agent_name': agent.get('name'),
                                    'email': agent.get('name'),
                                    'login': agent.get('name'),
                                    'name': agent.get('name'),
                                    'campaign_details_id': camp_rec.id
                                })]

    def get_agents_list(self):
        TataControl = self.env['tatatele.connector']
        url = self.env.user.host + "v2/agents"
        # has_more_url = self.env.user.host + "v2/agents?has_more=true"
        # url = self.env.user.host + "v2/agents/groups"
        user = self.env.user
        agent_ids = []
        headers = {
            "accept": "application/json",
            "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzMDUyNzQiLCJpc3MiOiJodHRwczovL2Nsb3VkcGh"
                             "vbmUudGF0YXRlbGVzZXJ2aWNlcy5jb20vdG9rZW4vZ2VuZXJhdGUiLCJpYXQiOjE2OTg5Mjg5NjYsImV4cCI6MTk"
                             "5ODkyODk2NiwibmJmIjoxNjk4OTI4OTY2LCJqdGkiOiJUb3E1ckR6S3Q1dzBYSEppIn0.QaBSdPsr_ejLVpzbRKE"
                             "hBw7P_AYodAA7Xe9M6-UyBjA"}
        response = requests.request(
            url=url,
            # url=has_more_url,
            # data=request_data,
            headers=headers,
            method="GET"
        )
        if response.json().get('has_more'):
            data = response.json().get('data')
            agent_vals_list = []
            for agent_data in data:
                agent_ids.append(agent_data.get('id'))
                # updated_at_date = agent_data.get('updated_at').replace("T"," ")
                # updated_at = datetime.datetime.strptime(updated_at_date, '%Y-%m-%d %H:%M:%S%z')
                # created_at_date = agent_data.get('created_at').replace("T"," ")
                # created_at = datetime.datetime.strptime(created_at_date, '%Y-%m-%d %H:%M:%S%z')
                if not self.env['res.users'].search([('login', '=', agent_data.get('name'))]):
                    agent_vals_list.append({
                        'agent_id': agent_data.get('id'),
                        'eid': agent_data.get('eid'),
                        'agent_name': agent_data.get('name'),
                        'name': agent_data.get('name'),
                        'login': agent_data.get('name'),
                        'email': agent_data.get('name'),
                        'follow_me_number': agent_data.get('follow_me_number'),
                        'intercom': agent_data.get('intercom'),
                        'custom_status': agent_data.get('custom_status'),
                        'alternate_numbers': agent_data.get('alternate_numbers'),
                        'is_login_based_calling_enabled': agent_data.get('is_login_based_calling_enabled'),
                        'timegroup_id' : agent_data.get('timegroup'),
                        'calls_answered': agent_data.get('call_stats').get('call_answered'),
                        'calls_missed': agent_data.get('call_stats').get('call_missed'),
                        'departmentid': agent_data.get('departments'),
                        'is_verified': agent_data.get('is_verified'),
                        'team_id': agent_data.get('team_id'),
                        'team_name': agent_data.get('team_name'),
                        'updated_at': datetime.datetime.strptime(agent_data.get('updated_at').split("T")[0], '%Y-%m-%d'),
                        'created_at': datetime.datetime.strptime(agent_data.get('created_at').split("T")[0], '%Y-%m-%d'),
                    })

            users = self.env['res.users'].create(agent_vals_list)
            access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzMDUyNzQiLCJpc3MiOiJodHRwczovL2Nsb3VkcGhvbmUudGF0YXRlbGVzZXJ2aWNlcy5jb20vdG9rZW4vZ2VuZXJhdGUiLCJpYXQiOjE2OTg5Mjg5NjYsImV4cCI6MTk5ODkyODk2NiwibmJmIjoxNjk4OTI4OTY2LCJqdGkiOiJUb3E1ckR6S3Q1dzBYSEppIn0.QaBSdPsr_ejLVpzbRKEhBw7P_AYodAA7Xe9M6-UyBjA"
            agent_headers = {
                "accept": "application/json",
                "Authorization": 'Bearer %s' % access_token}
            for agent_id in agent_ids:
                agent_id_url = self.env.user.host + "v2/agent/%s" % agent_id
                response = requests.request(
                    url=agent_id_url,
                    headers=agent_headers,
                    method="GET"
                ).json()
        return

    def get_call_records_detail(self):
        list_call_details = []
        shortner = pyshorteners.Shortener()
        TataControl = self.env["tatatele.connector"]
        # config = self.env["tatatele.configuration"].search([], limit=1)
        user = self.env.user
        if not (user.tata_email and user.tata_password and user.access_token):
            raise UserError(
                _("No Tata TeleService Configuration Added. Please Check !")
            )

        # list_url = "https://api-smartflo.tatateleservices.com/v1/call/records"
        list_url = "https://api-smartflo.tatateleservices.com/v1/call/records?limit=300?page=2?from_date={}&to_date={}".format(
            fields.Datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
            (fields.Datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        )
        get_call_record_details = TataControl.call(
            user, request_url=list_url, verb="GET"
        )
        if isinstance(get_call_record_details.json(), dict):
            list_call_details.append(get_call_record_details.json())
        call_rec = {}
        if isinstance(list_call_details[0].get("results"), list):
            for call_detail in list_call_details[0].get("results"):
                existed_call_id = self.env["call.record.details"].search(
                    [
                        ("is_call_detail_import", "=", False),
                        ("call_record_id", "=", call_detail.get("id")),
                    ]
                )
                if not existed_call_id:
                    print("call_detail", call_detail)
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
                            "broadcast_id": self.env['broadcast.list'].search([('broadcastid', '=', call_detail.get("broadcast_id", False))], limit=1).id,
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
                            "disposition_name": call_detail.get('dialer_call_details') and call_detail.get('dialer_call_details').get('disposition_name'),
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
                self.env["call.record.details"].create(call_rec)
        else:
            self.env.user.generate_access_token()
            self.get_call_records_detail()

    def _create_lead_details(self, vals):
        print("_create_lead_details--------")
        lead = self.env["lead.details"].create(vals)
        return lead

    def get_lead_lists(self):
        print("get_lead_lists--------------")
        _logger.info("get_lead_lists>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.with_delay().fetch_lead_lists()

    def fetch_lead_lists(self):
        print("fetch_lead_lists method calling-----------")
        _logger.info("\n\n\nfetch_lead_lists>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        TataControl = self.env['tatatele.connector']
        # list_url = "https://api-smartflo.tatateleservices.com/v1/broadcast/leads/242781"
        # list_url = "https://api-smartflo.tatateleservices.com/v1/broadcast/leads/241192"

        user = self.env.user
        if not (user.tata_email and user.tata_password and user.access_token):
            raise UserError(
                _("No Tata TeleService Configuration Added. Please Check !")
            )
        # TataConfig.generate_access_token()
        # lists = self.env['broadcast.list'].search([], limit=32, order='id DESC')
        lists = self.env['broadcast.list'].search([])

        if not lists:
            self.fetch_lead()
        else:
            list_lead_details = []
            for list in lists:
                list_url = self.env.user.host + "v1/broadcast/leads/%s" % list.list_id
                # list_urlll = "https://api-smartflo.tatateleservices.com/v1/broadcast/leads/241192"

                get_lists_lead = TataControl.call(user, request_url=list_url, verb="GET")
                if get_lists_lead.status_code == 401:
                    self.env.user.generate_access_token()
                if isinstance(get_lists_lead.json(), dict):
                    continue
                _logger.info("\n\nget_lists_lead.status_code>>>>>>>>>>%s", get_lists_lead.status_code)
                if get_lists_lead.status_code == 200:
                    if not isinstance(get_lists_lead.json(), dict):
                        list_lead_details.append(get_lists_lead.json())
                        for data in get_lists_lead.json():
                            exist_lead_id = self.env["lead.details"].sudo().search([
                                ('lead_id', '=', data.get('id'))
                            ])
                            if data.get('lead_picked') != 0 and not exist_lead_id:
                                lead_vals = {
                                    "lead_id": data.get("id"),
                                    "listId": data.get("list_id"),
                                    'broadcast_list_id': self.env['broadcast.list'].search(
                                        [('list_id', '=', list.list_id)], limit=1).id,
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
                                lead = self._create_lead_details(lead_vals)
                                _logger.info("\n\n\nget_lead_lists>>>>>>>>>>>>>>>>>>>>>>>>>>>\n%s", lead)

    def fetch_lead(self):
        BroadcastList = self.env["broadcast.list"]
        TataControl = self.env["tatatele.connector"]
        user = self.env.user
        lead_url = user.host + "v1/broadcast/lists"
        list_Leads = TataControl.call(user, request_url=lead_url, verb="GET")
        if list_Leads.status_code == 200:
            list_leads_vals = list_Leads.json()
            list_lead_vals = [
               {"list_id": list_lead.get("id"), "name": list_lead.get('name')} for list_lead in list_leads_vals
            ]
            new_lead_list_id = []
            for new_lead_id in list_lead_vals:
                lead_list_id = BroadcastList.search([("list_id", "=", new_lead_id.get("list_id"))])
                if not lead_list_id:
                    new_lead_list_id.append({"list_id": new_lead_id.get("list_id"), "name": new_lead_id.get('name')})
            if new_lead_list_id:
                BroadcastList.create(new_lead_list_id)
        else:
            raise UserError(
                _("No Tata TeleService Configuration Added. Please Check !"))

    def get_users(self):
        multiple_user_url = "https://api-cloudphone.tatateleservices.com/v1/users"
        users_details = []
        headers = {
            "accept": "application/json",
            "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzMDM5OTQiLCJpc3MiOiJodHRwczovL2Nsb3VkcGhvbmUudGF0YXRlbGVzZXJ2aWNlcy5jb20vdG9rZW4vZ2VuZXJhdGUiLCJpYXQiOjE2OTcwMDc4MzcsImV4cCI6MTk5NzAwNzgzNywibmJmIjoxNjk3MDA3ODM3LCJqdGkiOiJKOVNFcFVSUGxKaGk4VDJwIn0.FA_iPrkNuSskOo7UBAW7Xg5jLGaa9aGnHm3Zl41ZHpc"
        }
        user_response = requests.request(headers=headers, url=multiple_user_url, method="GET")
        json_to_dict = json.loads(user_response.text)

        if user_response.status_code == 200:
            if isinstance(json_to_dict, dict):
                users_details.append(user_response.json())
        else:
            message = user_response.json()
            raise UserError(_(message.get('message')))

    def get_departments(self):
        TataControl = self.env["tatatele.connector"]
        Department = self.env["tatatele.department"]
        user = self.env.user
        department_url = user.host + "v1/departments"
        user = self.env.user
        if not (user.tata_email and user.tata_password and user.access_token):
            raise UserError(
                _("No Tata TeleService Configuration Added. Please Check !")
            )
        department_response = TataControl.call(user, request_url=department_url, verb="GET")
        if department_response.status_code == 401:
            self.env.user.generate_access_token()
        vals = {}
        if isinstance(department_response.json(), list):
            for department in department_response.json():
                if not Department.filtered(lambda x: x.id == department.get('id')):
                    vals.update({
                        "departmentid": department.get('id'),
                        "name": department.get('name'),
                        "description": department.get('description'),
                        "ring_strategy": department.get('ring_strategy'),
                        "agent_count": department.get('agent_count'),
                        "calls_answered": department.get('calls_answered'),
                        "calls_missed": department.get('calls_answered'),
                        "use_as_queue": department.get('use_as_queue'),
                        "queue_timeout": department.get('queue_timeout'),
                        # "agent_ids": [(0, 0, {"tatatele_department_id": agent.get('id') for agent in department.get('agents')})],
                    })
                    Department.create(vals)

