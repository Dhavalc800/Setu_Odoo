from odoo import fields, models, api, _, registry, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import AccessDenied
import requests
import json
from datetime import datetime, timedelta
import logging
import time, threading

_logger = logging.getLogger(__name__)


class User(models.Model):
    _inherit = 'res.users'

    host = fields.Char(
        "Host", default="https://api-smartflo.tatateleservices.com/"
    )
    active = fields.Boolean("Active", default=True)
    access_token = fields.Char("Access Token")
    tata_email = fields.Char(string="Tatatele Email")
    tata_password = fields.Char(string="Tatatele Password")
    agent_id = fields.Char(string="AgentID")
    agent_extension_id = fields.Char(string="Agent Extension")
    agent_name = fields.Char(string="Agent Name")
    follow_me_number = fields.Char(string="Follow Me Number")
    alternate_numbers = fields.Char(string="Alternate Number")
    intercom = fields.Char(string="Intercom")
    custom_status = fields.Char(string="Custom Status")
    is_verified = fields.Boolean(string="Is Verified")
    is_login_based_calling_enabled = fields.Boolean(string="Is Login Based Calling Enabled")
    timegroup_id = fields.Char(string="Time Group")
    timegroup_name = fields.Char(string="Time Group Name")
    call_stats = fields.Char(string="Call Stats")
    calls_answered = fields.Char(string="Calls Answered")
    calls_missed = fields.Char(string="Calls Missed")
    tatatele_department_id = fields.Many2one("tatatele.department", "Department")
    departmentid = fields.Char(string="Department ID")
    department_name = fields.Char(string="Department Name")
    eid = fields.Char(string="EID")
    campaign_details_id = fields.Many2one('campaign.details')
    team_id = fields.Char('Team ID')
    team_name = fields.Char("Team Name")
    updated_at = fields.Datetime("Updated At")
    created_at = fields.Datetime("Created At")
    tatateleuserid = fields.Char("User ID")
    last_seen_id = fields.Integer("Last Seen ID")
    time_out = fields.Char("Timeouts")
    is_tatatele_admin = fields.Boolean(string="Is Tata Tele Admin User")
    is_created_from_multiple_user_api = fields.Boolean(help="This is to check whether the user is created from multiple user "
                                                    "api or not")
    agent_number = fields.Char(string="Agent Number")

    @api.constrains('is_tatatele_admin')
    def check_is_tatatele_admin(self):
        for rec in self:
            if rec.is_tatatele_admin:
                admin_user = rec.search([('is_tatatele_admin', '=', True), ('id', '!=', rec.id)])
                if admin_user:
                    raise ValidationError(_("There can be only one Admin User. For Now %s User is admin user ." % admin_user.name))

    def generate_access_token(self):
        TataControl = self.env['tatatele.connector']
        if self.tata_email and self.tata_password and self.host:
            self.access_token = False
            url = self.host + "v1/auth/login"
            # email = "Lalit@142"
            # password = "Setu@123"
            value = {"email": self.tata_email, "password": self.tata_password}
            access_auth = TataControl.call(self, request_url=url, verb="POST", payload=value)
            self.access_token = access_auth.json().get('access_token')
            threading.Timer(3600, TataControl.call(self, request_url=url, verb="POST", payload=value)).start()
            return access_auth
        else:
            raise ValidationError(
                _("No Tata TeleService Configuration Added. Please Check !"))

    def _cron_fetch_multiple_user(self):
        # multiple_user_url = "https://api-cloudphone.tatateleservices.com/v1/users?last_seen_id=319313&limit=100"
        multiple_user_url = "https://api-cloudphone.tatateleservices.com/v1/users"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzMDUyNzQiLCJpc3MiOiJodHRwczovL2Nsb"
                             "3VkcGhvbmUudGF0YXRlbGVzZXJ2aWNlcy5jb20vdG9rZW4vZ2VuZXJhdGUiLCJpYXQiOjE2OTg5Mjg5NjYsImV4cC"
                             "I6MTk5ODkyODk2NiwibmJmIjoxNjk4OTI4OTY2LCJqdGkiOiJUb3E1ckR6S3Q1dzBYSEppIn0.QaBSdPsr_ejLVpz"
                             "bRKEhBw7P_AYodAA7Xe9M6-UyBjA"
        }
        # last_seen_id = 1
        ###############
        """
        last_seen_id: The uniqueid of the agent till which records have been fetched. For example, last_seen_id=14805
         then the agents from 14806 will be displayed.
        """
        ###############
        user_vals = {}
        last_seen_id = self.env.user.last_seen_id or 1
        multiple_user_lastseen_url = f"{multiple_user_url}?last_seen_id={last_seen_id}&limit=100"
        user_response = requests.get(url=multiple_user_lastseen_url, headers=headers)
        if user_response.status_code == 200:
            json_data = user_response.json()
            self.env['ir.config_parameter'].sudo().set_param("fetch_multiple_user", True)
            if isinstance(json_data, dict):
                last_seen_id = json_data.get('last_seen_id')
                if not last_seen_id == None:
                    self.env.user.last_seen_id = last_seen_id
                for datas in json_data.values():
                    if isinstance(datas, list):
                        for data in datas:
                            user_vals.update({
                                'tatateleuserid': data.get('id'),
                                'agent_id': data.get('agent', {}).get('id'),
                                'agent_name': data.get('agent', {}).get('name', ''),
                                'follow_me_number': data.get('agent', {}).get('follow_me_number', ''),
                                'login': data.get('login_id'),
                                'name': data.get('name') or data.get('login_id'),
                                'is_login_based_calling_enabled': data.get('is_login_based_calling_enabled'),
                                # query for below field's values
                                'agent_extension_id': data.get('extension'),
                                'custom_status': data.get('user_status'),
                                'is_created_from_multiple_user_api': True,
                            })
                            tatauserid_rec = self.search([('tatateleuserid', '=', data.get('id'))])
                            if tatauserid_rec:
                                tatauserid_rec.write(user_vals)
                            else:
                                existing_users = self.search([('login', '=', user_vals.get('login'))])
                                if existing_users:
                                    existing_users.write(user_vals)
                                else:
                                    self.create(user_vals)
                                    # _logger.info("Users after this last_seen_id exists")
            else:
                self.env['ir.config_parameter'].sudo().set_param("fetch_multiple_user", False)
                if not self.env['ir.config_parameter'].sudo().get_param("fetch_multiple_user"):
                    tatauser_cron = self.env['ir.cron'].sudo().env.ref('scs_tatatele_integration.tata_multiple_users_cron')
                    tatauser_cron.nextcall = (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        else:
            _logger.error(f"HTTP request failed with status code: {user_response.status_code}")
        return

    def fetch_tatauser_details(self, TATA_userID):
        user_vals = {}
        for userID in TATA_userID:
            url = "https://api-cloudphone.tatateleservices.com/v1/user/%s" % (userID)
            headers = {
                "accept": "application/json",
                "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzMDUyNzQiLCJpc3MiOiJodHRwczovL2Nsb"
                                 "3VkcGhvbmUudGF0YXRlbGVzZXJ2aWNlcy5jb20vdG9rZW4vZ2VuZXJhdGUiLCJpYXQiOjE2OTg5Mjg5NjYsImV4cC"
                                 "I6MTk5ODkyODk2NiwibmJmIjoxNjk4OTI4OTY2LCJqdGkiOiJUb3E1ckR6S3Q1dzBYSEppIn0.QaBSdPsr_ejLVpz"
                                 "bRKEhBw7P_AYodAA7Xe9M6-UyBjA"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    user_details = data['data']
                    user_vals.update({
                        'tatateleuserid': user_details['id'],
                        'name': user_details['name'],
                        'follow_me_number': user_details['number'],
                        # 'team': user_details['team_member'],
                        'is_login_based_calling_enabled': user_details['team_member']['is_login_based_calling'],
                        'agent_id': user_details['agent']['id'],
                        'intercom': user_details['agent']['intercom'],
                        'agent_number': user_details['agent']['number'],
                    })
                    user_id = self.search([('tatateleuserid', '=', user_details['id'])], limit=1)
                    if user_id:
                        user_id.write(user_vals)

    def action_update_tata_user_details(self):
        tata_user_id = []
        blank_tata_user_id = []
        for rec in self:
            if not rec.tatateleuserid:
                blank_tata_user_id.append(rec.name)
            else:
                tata_user_id.append(rec.tatateleuserid)
        if blank_tata_user_id:
            raise ValidationError(_("Please Enter Tata User ID for %s \n to fetch their details.") % (', '.join(blank_tata_user_id)))
        else:
            if tata_user_id:
                self.with_delay().fetch_tatauser_details(tata_user_id)
        return


class Partner(models.Model):
    _inherit = 'res.partner'

    def click_to_call(self):
        if not self.phone:
            raise ValidationError(_("please Enter Phone number to make a call"))
        if not self.env.user.follow_me_number:
            raise ValidationError(_("Please Add number in Follow me number field of user to make a call"))
        call_url = self.env.user.host + 'v1/click_to_call'
        headers = {
            "accept": "application/json",
            "Authorization": self.env.user.access_token,
            "content-type": "application/json"
        }
        payload = {
            # "agent_number": self.user_id.agent_extension_id,
            # "agent_number": "917969323082",
            "agent_number": self.env.user.follow_me_number,
            "destination_number": self.phone
        }
        response = requests.post(call_url, json=payload, headers=headers)
        if response.status_code == 401:
            self.env.user.generate_access_token()
        # elif not response.status_code == 200:
        #     msg = response.json().get("message")
            # raise UserError(_(msg))
        msg = response.json().get("message")
        notify = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(msg),
                'sticky': False,
            }
        }
        return notify
