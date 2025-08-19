from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError
import mysql.connector
import logging
import urllib.parse
from urllib.parse import quote
_logger = logging.getLogger(__name__)
import requests

import time
import random


class FetchLeadUser(models.TransientModel):
    _name = 'fetch.lead.user'
    _description = "Fetch Lead User"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "lead_id"

    call_id = fields.Char('Call ID')
    lead_id = fields.Many2one('lead.data.lead', tracking=True, string="Lead", readonly=True)
    campaigns_id = fields.Many2one(related="lead_id.campaign_id", string=" Lead Campaign")
    campaigns_ids = fields.Many2many(
        'campaigns.list',
        string="Assigned Campaigns",
        compute='_compute_campaigns_ids',
        store=False
    )
    dynamic_field_values = fields.Text(
        string="Lead Data",
        readonly=True,
        tracking=True,
        compute="_compute_dynamic_field_values"
    )
    disposition_id = fields.Many2one('dispo.list.name', tracking=True, string="Select Disposition")
    allowed_disposition_ids = fields.Many2many(
        'dispo.list.name',
        tracking=True,
        string="Allowed Dispositions",
        compute="_compute_allowed_dispositions"
    )
    remark = fields.Text(string="Remark", tracking=True)
    call_history_ids = fields.One2many(
        'lead.call.history', 'lead_id',
        string='Today\'s Call History',
        tracking=True,
        # compute='_compute_call_history',
        store=False
    )
    show_all_callbacks = fields.Boolean(
        string="Show All Callbacks",
        default=False,
        help="Toggle to show all callbacks instead of just this week's"
    )
    call_time = fields.Datetime(string='Call Time', default=fields.Datetime.now)
    opportunity_name = fields.Char(string="Opportunity Name", tracking=True)
    expected_revenue = fields.Float(string="Expected Revenue", tracking=True)

    is_disposition_interested = fields.Boolean(
        string="Is Interested Disposition",
        compute="_compute_is_disposition_interested"
    )
    is_disposition_callback = fields.Boolean(compute="_compute_is_callback", store=False)
    callback_datetime = fields.Datetime(string="Callback Date/Time", tracking=True)
    callback_lead_info = fields.Text(string="Call Back Details", tracking=True)
    # callback_lead_ids = fields.Many2many('lead.callback.info', string="Callback Leads", tracking=True)
    callback_lead_ids = fields.Many2many(
        'lead.callback.info', 
        string="Callback Leads",
        compute='_compute_callback_leads',
        store=False
    )
    campaigns_count = fields.Integer(
        string="Assigned Campaigns Count",
        compute='_compute_campaigns_ids',
        store=False
    )
    has_callback_lead = fields.Boolean(compute="_compute_has_callback_lead", store=False)
    pending_callback_lead_ids = fields.Many2many(
        'lead.callback.info',
        compute='_compute_pending_callback_lead_ids',
        string='Pending Callbacks',
        store=False
    )
    user_lead_id = fields.Many2one('lead.data.lead', string="User Current Lead")
    phone_link_html = fields.Html(string="Call Link", compute="_compute_phone_link_html")
    search_number = fields.Char(string="Search Number")
    searched_lead_id = fields.Many2one('lead.data.lead', string="Searched Lead", compute="_compute_searched_lead", store=False)
    show_warning = fields.Boolean(string="Show Warning", default=False)
    warning_message = fields.Char(string="Warning")
    inbound_call_ids = fields.One2many(
        'inbound.call.temp',
        'lead_fetch_id',
        string="Inbound Calls"
    )

    # def write(self, vals):
    #     disposition_changed = 'disposition_id' in vals
    #     result = super(FetchLeadUser, self).write(vals)

    #     if result and disposition_changed:
    #         for rec in self:
    #             if rec.lead_id and rec.disposition_id:
    #                 self.env['disposition.queue'].create({
    #                     'lead_id': rec.lead_id.id,
    #                     'campaign_id': rec.lead_id.campaign_id.id if rec.lead_id.campaign_id else False,
    #                     'lead_list_id': rec.lead_id.lead_list_id.id if rec.lead_id.lead_list_id else False,
    #                     'disposition_id': rec.disposition_id.id,
    #                     'call_by': self.env.user.id,
    #                     'disposition_time': fields.Datetime.now(),
    #                     'disposition_from': 'From Fetch Lead',
    #                 })

    #     return result

    @api.depends()
    def _compute_campaigns_ids(self):
        for rec in self:
            campaigns = self.env['campaigns.list'].search([('user_ids', 'in', self.env.uid)])
            rec.campaigns_ids = campaigns
            rec.campaigns_count = len(campaigns)

    def _compute_callback_leads(self):
        for record in self:
            # All valid callbacks
            record.callback_lead_ids = self.env['lead.callback.info'].search([
                ('user_id', '=', self.env.user.id),
                ('disposition_id.show_in_callback', '=', True)
            ])
            
            # Only pending (future) callbacks
            record.pending_callback_lead_ids = self.env['lead.callback.info'].search([
                ('user_id', '=', self.env.user.id),
                ('disposition_id.show_in_callback', '=', True),
                ('callback_time', '>=', fields.Datetime.now())
            ])

    
    def action_send_whatsapp(self):
        for rec in self:
            phone = rec.lead_id.x_phone
            if not phone:
                raise ValidationError("No phone number found for this lead.")

            # Clean up the phone number
            phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            
            if not phone_clean.startswith('+'):
                phone_clean = '+91' + phone_clean
            if phone_clean.startswith('+'):
                phone_clean = phone_clean[1:]

            message = f"Hello {rec.lead_id.x_name}, this is from Setu!"
            encoded_message = quote(message)
            url = f"https://wa.me/{phone_clean}?text={encoded_message}"

            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }

    # @api.model
    # def default_get(self, fields_list):
    #     res = super(FetchLeadUser, self).default_get(fields_list)
    #     res['inbound_call_ids'] = self._get_inbound_calls()
    #     return res

    @api.depends("disposition_id")
    def _get_inbound_calls(self):
        config = self.env['ir.config_parameter'].sudo()
        host = config.get_param('external_db.mysql_host')
        user = config.get_param('external_db.mysql_user')
        password = config.get_param('external_db.mysql_password')
        database = config.get_param('external_db.mysql_database')

        inbound_call_objs = []

        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            cursor = conn.cursor(dictionary=True)

            today = datetime.today()
            last_week = today - timedelta(days=6)

            today_str = today.strftime("%d/%m/%Y")
            last_week_str = last_week.strftime("%d/%m/%Y")
            user_mobile = self.env.user.employee_id.mobile_phone or ''
            mobile_last10 = user_mobile[-10:]

            # cursor.execute("""
            #     SELECT Caller_Number, Destination_Number, Date, Call_Type, Overall_Call_Status, Recording FROM airtel.call_details
            #     WHERE STR_TO_DATE(Date, '%d/%m/%Y') 
            #         BETWEEN STR_TO_DATE(%s, '%d/%m/%Y') AND STR_TO_DATE(%s, '%d/%m/%Y')
            #     AND RIGHT(Destination_Number, 10) = %s
            #     AND Call_Type = 'inbound'
            #     AND Overall_Call_Status = 'Answered' LIMIT 100
            # """, (last_week_str, today_str, mobile_last10))

            cursor.execute("""
                SELECT * FROM airtel.call_details
                WHERE STR_TO_DATE(Date, '%d/%m/%Y') 
                    BETWEEN STR_TO_DATE(%s, '%d/%m/%Y') AND STR_TO_DATE(%s, '%d/%m/%Y')
                AND RIGHT(Destination_Number, 10) = %s
                AND Call_Type = 'inbound'
                AND Overall_Call_Status = 'Answered'
            """, (last_week_str, today_str, mobile_last10))

            inbound_calls = cursor.fetchall()
            cursor.close()
            conn.close()

            unique_phones = set()

            for call in inbound_calls:
                raw_phone = call.get('Caller_Number') or ''
                phone_last10 = raw_phone.lstrip('0')[-10:]
                recording = call.get('Recording')

                if phone_last10 in unique_phones:
                    continue
                unique_phones.add(phone_last10)

                lead = self.env['lead.data.lead'].search([("x_phone", '=', phone_last10)], limit=1)

                has_interested_dispo = self.env['lead.call.history'].search_count([
                    ('phone', 'ilike', phone_last10),
                    ('disposition_id.is_intrested', '=', True)
                ], limit=1)
                if has_interested_dispo:
                    continue

                active_fetch = self.env['fetch.lead.user'].search_count([
                    ('lead_id.x_phone', 'ilike', phone_last10),
                    ('disposition_id', '=', False)
                ])
                if active_fetch:
                    continue

                inbound_call_objs.append((0, 0, {
                    'lead_id': lead.id,
                    'phone': phone_last10,
                    'caller_number': raw_phone,
                    'call_type': 'inbound',
                    'recording': recording,
                }))

        except mysql.connector.Error as err:
            _logger.error("MySQL connection error: %s", err)

        return inbound_call_objs

    @api.depends('search_number')
    def _compute_searched_lead(self):
        for record in self:
            record.searched_lead_id = False
            if record.search_number:
                lead = self.env['lead.data.lead'].search([('x_phone', 'ilike', record.search_number)], limit=1)
                if lead:
                    record.searched_lead_id = lead

    def action_set_searched_lead(self):
        for rec in self:
            if rec.searched_lead_id:
                rec.lead_id = rec.searched_lead_id


    @api.depends('lead_id')
    def _compute_dynamic_field_values(self):
        for rec in self:
            if rec.lead_id:
                model_fields = self.env['ir.model.fields'].sudo().search([
                    ('model', '=', 'lead.data.lead'),
                    ('name', 'like', 'x_')
                ])
                label_map = {f.name: f.field_description for f in model_fields}

                dynamic_data = ""
                for field in rec.lead_id._fields:
                    if field.startswith('x_') and hasattr(rec.lead_id, field):
                        value = getattr(rec.lead_id, field, '')
                        if value:
                            label = label_map.get(field, field)
                            dynamic_data += f"{label}: {value}\n"
                rec.dynamic_field_values = dynamic_data
            else:
                rec.dynamic_field_values = ''

    # @api.depends('lead_id.x_phone', 'dynamic_field_values')
    # def _compute_phone_link_html(self):
    #     for record in self:
    #         phone = record.lead_id.x_phone
    #         lead_id = record.lead_id.id
    #         if phone:
    #             formatted = phone.replace(" ", "")
    #             call_id = record.env.user.employee_id.identification_no or ''
    #             dynamic_values = record.dynamic_field_values or ''
    #             dynamic_encoded = urllib.parse.quote(dynamic_values)
                
    #             # Include fetch_lead_id (current record ID) in the URL
    #             fetch_lead_id = record.id
                
    #             record.phone_link_html = f"""
    #                 <a href="/setu_dialer/make_call?call_id={call_id}&number={formatted}&id={record.id}&model={record._name}&lead_id={lead_id}&dynamic_values={dynamic_encoded}&fetch_lead_id={fetch_lead_id}"
    #                 class="btn btn-primary" 
    #                 style="padding: 8px 16px; border-radius: 6px;">
    #                 📞 Call
    #                 </a>
    #             """
    #         else:
    #             record.phone_link_html = '<span class="text-danger">No phone number</span>'

    def action_make_call(self):
        for record in self:
            try:
                # Ensure required fields are available, use correct field for phone number
                if not record.lead_id.x_phone:
                    raise UserError(_("Missing phone number"))

                # Check if the employee_id and identification_no are available
                if not record.env.user.employee_id:
                    raise UserError(_("Employee record not found for user"))
                call_id = record.env.user.employee_id.identification_no or ''
                
                if not call_id:
                    raise UserError(_("Missing identification number for employee"))

                _logger.info(f"Making call with ID: {call_id}, to number: {record.lead_id.x_phone.strip()}")

                # Prepare parameters for the HTTP call
                api_url = 'https://bksetu-employees.setudigital.com/api/call'

                # Serialize lead_id attributes to basic data types (e.g., ID, name)
                lead_data = {
                    "id": record.lead_id.id,
                    "name": record.lead_id.display_name,  # Assuming you want to send the name
                    "x_phone": record.lead_id.x_phone,  # Assuming x_phone is the phone field
                    "dynamic_values": record.lead_id.dynamic_field_values,
                }
                
                raw_dynamic_values = record.lead_id.dynamic_field_values
            
                # Initialize dynamic_values with required fields
                dynamic_values = {
                    'fetch_lead_id': record.id if record.id else '',
                    'user_id': record.env.user.id,  # Add current user ID
                    'user_name': record.env.user.name  
                }

                # Decode and merge additional dynamic values
                if raw_dynamic_values:
                    decoded_values = urllib.parse.unquote(raw_dynamic_values)
                    for line in decoded_values.strip().splitlines():
                        if ':' in line:
                            key, value = line.split(':', 1)
                            dynamic_values[key.strip()] = value.strip()

                payload = {
                    "id": call_id,
                    "number": record.lead_id.x_phone.strip(),
                    "lead_id": record.lead_id.id,
                    "user_id": record.env.user.id,
                    "dynamic_values": dynamic_values
                }

                _logger.debug(f"API Request Payload: {payload}")

                # Make the HTTP request to your custom route
                response = requests.post(api_url, json=payload, timeout=10)
                response.raise_for_status()  # Will raise an error if the request fails

                # Handle successful API response
                _logger.info(f"Call API success: {response.text}")
                
            except requests.exceptions.RequestException as e:
                _logger.error(f"API call failed: {str(e)}")
                raise UserError(_("Call failed to initiate. Please try again later."))
            except Exception as e:
                # Print exception for debugging purposes
                _logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                raise UserError(_("An unexpected error occurred"))



    # @api.depends('lead_id.x_phone', 'dynamic_field_values')
    # def _compute_phone_link_html(self):
    #     for record in self:
    #         phone = record.lead_id.x_phone
    #         lead_id = record.lead_id.id
    #         if phone:
    #             formatted = phone.replace(" ", "")
    #             call_id = record.env.user.employee_id.identification_no or ''
    #             dynamic_values = record.dynamic_field_values or ''
    #             dynamic_encoded = urllib.parse.quote(dynamic_values)

    #             record.phone_link_html = f"""
    #                 <a href="/setu_dialer/make_call?call_id={call_id}&number={formatted}&id={record.id}&model={record._name}&lead_id={lead_id}&dynamic_values={dynamic_encoded}" 
    #                 class="btn btn-primary" 
    #                 'target': 'self'
    #                 style="padding: 8px 16px; border-radius: 6px;">
    #                 📞 Call
    #                 </a>
    #             """
    #         else:
    #             record.phone_link_html = '<span class="text-danger">No phone number</span>'


    # @api.depends('lead_id.x_phone')
    # def _compute_phone_link_html(self):
    #     for record in self:
    #         phone = record.lead_id.x_phone
    #         if phone:
    #             formatted = phone.replace(" ", "")
    #             call_id = record.env.user.employee_id.identification_no
                
    #             record.phone_link_html = f"""
    #                 <a href="/setu_dialer/make_call?call_id={call_id}&number={formatted}&id={record.id}&model={record._name}" 
    #                 class="btn btn-primary" 
    #                 style="padding: 8px 16px; border-radius: 6px;">
    #                 📞 Call
    #                 </a>
    #             """
    #         else:
    #             record.phone_link_html = '<span class="text-danger">No phone number</span>'


    @api.depends('lead_id.x_phone')
    def _compute_phone_link_html(self):
        mobile_group = self.env.ref('setu_dialer.group_call_mobile')
        for record in self:
            phone = record.lead_id.x_phone
            if phone and mobile_group in record.env.user.groups_id:
                formatted = phone.replace(" ", "")
                record.phone_link_html = f"""
                    <a href="tel:+91{formatted}" style="
                        background-color: #1f8ef1;
                        color: white;
                        padding: 8px 16px;
                        text-decoration: none;
                        border-radius: 6px;
                        font-weight: bold;
                        display: inline-block;
                    ">📞 Call</a>
                """
            else:
                record.phone_link_html = ''

    def _compute_pending_callback_lead_ids(self):
        """Compute today's pending callbacks excluding fetched ones"""
        for record in self:
            today = fields.Date.context_today(record)
            start_dt = datetime.combine(today, datetime.min.time())
            end_dt = datetime.combine(today, datetime.max.time())

            domain = [
                ('user_id', '=', self.env.user.id),
                ('disposition_id.is_callback', '=', True),
                ('disposition_id.show_in_callback', '=', True),
                ('callback_time', '>=', start_dt),
                ('callback_time', '<=', end_dt),
                ('is_fetched_callback', '=', False)
            ]
            record.pending_callback_lead_ids = self.env['lead.callback.info'].search(domain, order='callback_time asc')


    @api.depends()
    def _compute_has_callback_lead(self):
        for rec in self:
            callback_lead = self.env['lead.callback.info'].search_count([
                ('user_id', '=', self.env.uid)
            ])
            rec.has_callback_lead = callback_lead > 0

    @api.depends('disposition_id')
    def _compute_is_callback(self):
        for rec in self:
            rec.is_disposition_callback = rec.disposition_id.is_callback if rec.disposition_id else False

    @api.depends('disposition_id')
    def _compute_is_disposition_interested(self):
        for rec in self:
            rec.is_disposition_interested = rec.disposition_id.is_intrested if rec.disposition_id else False

    def action_update_from_api(self, vals):
        """Update current record with API data"""
        self.ensure_one()
        return self.write(vals)

    # @api.depends('lead_id')
    def _compute_call_history(self):
        today = fields.Date.today()
        for rec in self:
            if rec.lead_id:
                rec.call_history_ids = self.env['lead.call.history'].search([
                    ('user_id', '=', self.env.uid),
                    ('call_time', '>=', datetime.combine(today, datetime.min.time())),
                    ('call_time', '<=', datetime.combine(today, datetime.max.time())),
                ])
            else:
                rec.call_history_ids = False

    def action_fetch_callback_lead(self):
        self.ensure_one()

        # ✅ Block if current lead is not disposed
        if self.lead_id:
            existing_history = self.env['lead.call.history'].search([
                ('user_id', '=', self.env.uid),
                ('lead_id', '=', self.lead_id.id),
            ], limit=1)
            if not existing_history:
                raise ValidationError("Please submit the current lead disposition before fetching a callback lead.")

        # ✅ Get all pending callback leads for this user
        CallHistory = self.env['lead.call.history']
        CallbackModel = self.env['lead.callback.info']
        all_callbacks = CallbackModel.search([
            ('user_id', '=', self.env.uid),
        ], order='callback_time asc')

        next_callback = False
        for cb in all_callbacks:
            # Check last disposition for this lead
            latest_dispo = CallHistory.search([
                ('lead_id', '=', cb.lead_id.id),
                ('user_id', '=', self.env.uid)
            ], limit=1, order="create_date desc")

            # Use if never submitted or last disposition is still callback
            if not latest_dispo or (latest_dispo.disposition_id and latest_dispo.disposition_id.is_callback):
                next_callback = cb
                break

        if not next_callback:
            raise ValidationError("No available callback leads. You might have already submitted all.")

        # ✅ Assign the lead
        self.lead_id = next_callback.lead_id
        self.callback_datetime = next_callback.callback_time

        # ✅ Load dynamic x_ fields with labels
        model_fields = self.env['ir.model.fields'].sudo().search([
            ('model', '=', 'lead.data.lead'),
            ('name', 'like', 'x_')
        ])
        label_map = {f.name: f.field_description for f in model_fields}

        dynamic_data = ""
        for field_name in label_map:
            value = getattr(self.lead_id, field_name, '')
            if value:
                label = label_map.get(field_name, field_name)
                dynamic_data += f"{label}: {value}\n"

        self.dynamic_field_values = dynamic_data

    def action_call_lead(self):
        if not self.lead_id.x_phone:
            raise ValidationError("Lead has no phone number.")
        return {
            'type': 'ir.actions.act_url',
            'url': f"tel:{self.lead_id.x_phone}",
            'target': 'self',
        }

    def action_call_back_lead(self):
        self.ensure_one()

        if self.disposition_id.is_callback and self.callback_datetime and self.lead_id:
            lead = self.lead_id

            # Check if the lead already exists for this user in callback info
            existing_cb = self.env['lead.callback.info'].search([
                ('lead_id', '=', lead.id),
                ('user_id', '=', self.env.user.id)
            ], limit=1)

            if existing_cb:
                # Just update the callback time
                existing_cb.callback_time = self.callback_datetime
                cb_lead = existing_cb
            else:
                # Create a new callback entry with campaign and lead list
                cb_lead = self.env['lead.callback.info'].create({
                    'lead_id': lead.id,
                    'callback_time': self.callback_datetime,
                    'user_id': self.env.user.id,
                    'disposition_id': self.disposition_id.id,
                    'call_time': fields.Datetime.now(),
                    'remark': self.remark,
                    'campaign_id': lead.lead_list_id.campaign_id.id if lead.lead_list_id else False,
                    'lead_list_id': lead.lead_list_id.id if lead.lead_list_id else False,
                })

            # Link the record to the wizard's one2many field
            self.callback_lead_ids = [(4, cb_lead.id)]

            # Call fetch_and_store_call_details for the callback lead
            # if lead.x_phone:
            #     self._fetch_and_store_call_details(lead.x_phone)

            # Clear fields so user can fetch the next lead
            self.lead_id = False
            self.dynamic_field_values = ""
            self.remark = ""
            self.disposition_id = False
            self.callback_datetime = False

    @api.depends('lead_id')
    def _compute_allowed_dispositions(self):
        for rec in self:
            rec.allowed_disposition_ids = rec.lead_id.lead_list_id.campaign_id.disposition_id.disposition_ids or self.env['dispo.list.name']

    def action_submit_disposition(self, user=None):
        config = self.env['ir.config_parameter'].sudo()
        mysql_checker = config.get_param('external_db.mysql_checker')
        lead_user = self.env['res.users'].sudo().browse(user)
        if not lead_user:
            lead_user = self.env.user
        # Check Callback
        callback = self.env['lead.callback.info'].search([('lead_id', '=', self.lead_id.id)], limit=1)
        if callback and self.disposition_id.is_intrested:
            callback.write({'is_fetched_callback': True})

        for record in self:
            if not record.disposition_id:
                raise ValidationError("Please select a disposition.")

            # ✅ Check if disposition already submitted for this lead by this user
            already_exists = self.env['lead.call.history'].search_count([
                ('lead_id', '=', record.lead_id.id),
                ('user_id', '=', lead_user.id)
            ])
            # if already_exists:
            #     raise ValidationError("You have already submitted a disposition for this lead.")

            # ✅ Create call history
            lead = record.lead_id

            # self.env['lead.call.history'].create({
            #     'lead_id': lead.id,
            #     'disposition_id': record.disposition_id.id,
            #     'user_id': self.env.uid,
            #     'call_time': fields.Datetime.now(),
            #     'remark': record.remark,
            #     'campaign_id': lead.lead_list_id.campaign_id.id if lead.lead_list_id else False,
            #     'lead_list_id': lead.lead_list_id.id if lead.lead_list_id else False,
            #     'phone': lead.x_phone or lead.phone,
            # })
            # ✅ Always create Lead Call History, but fields depend on is_intrested
            call_history_vals = {
                'lead_id': lead.id,
                'disposition_id': record.disposition_id.id,
                'user_id': lead_user.id,
                'call_time': fields.Datetime.now(),
                'remark': record.remark,
                'campaign_id': lead.lead_list_id.campaign_id.id if lead.lead_list_id else False,
                'lead_list_id': lead.lead_list_id.id if lead.lead_list_id else False,
                'phone': lead.x_phone,
            }

            # ➡️ If Interested, add expected_revenue and description
            if record.disposition_id.is_intrested:
                call_history_vals.update({
                    'opportunity_name': record.opportunity_name,
                    'expected_revenue': record.expected_revenue or '',
                })

            # 🔁 Get sales team of user (assuming 1 team per user)
            sales_team = self.env['crm.team'].search([('member_ids', 'in', [lead_user.id])], limit=1)
            branch_manager = sales_team.branch_manager_id if sales_team else False

            # 📝 Create Branch Manager Submission record
            # self.env['branch.manager.assignment'].create({
            #     'lead_id': record.lead_id.id,
            #     # 'source': record.lead_id.x_source or '',
            #     # 'phone': record.lead_id.x_phone,
            #     'disposition_id': record.disposition_id.id,
            #     'call_by': lead_user.id,
            #     'opportunity_name': record.opportunity_name or '',
            #     'expected_revenue': record.expected_revenue or 0.0,
            #     # 'service': record.lead_id.x_service or '',  # Replace with the correct dynamic field
            #     'call_date_time': fields.Datetime.now(),
            #     'branch_manager_id': branch_manager.id if branch_manager else False,
            #     'team_id': sales_team.id if sales_team else False,
            # })
    
            self.env['lead.call.history'].create(call_history_vals)

            # recording_matched = False
            # if record.lead_id.x_phone:
            #     recording_matched = self._fetch_and_store_call_details(record.lead_id.x_phone)
            # if not recording_matched and mysql_checker:
            #     raise ValidationError("No matching call record found. You must call the lead before submitting the disposition.")

            # ✅ If the disposition is marked as DND and not already in DND list
            if record.disposition_id.is_dnd and record.lead_id.x_phone:
                if not self.env['lead.dnd'].search([('phone', '=', record.lead_id.x_phone)]):
                    self.env['lead.dnd'].create({
                        'name': record.lead_id.x_name,
                        'email': record.lead_id.x_email,
                        'phone': record.lead_id.x_phone,
                    })

            if record.disposition_id.is_intrested:
                if not record.opportunity_name or not record.expected_revenue:
                    raise ValidationError("Please provide Opportunity Name and Expected Revenue.")

                partner_obj = self.env['res.partner']
                lead_name = record.lead_id.x_name or ''
                lead_email = record.lead_id.x_email or ''
                lead_phone = record.lead_id.x_phone or ''

                # 🔍 Try to find existing partner by phone or email
                partner = partner_obj.search([
                    '|',
                    ('phone', '=', lead_phone),
                    ('email', '=', lead_email)
                ], limit=1)

                # 🧾 If not found, create a new partner
                if not partner:
                    partner = partner_obj.create({
                        'name': lead_name,
                        'email': lead_email,
                        'phone': lead_phone,
                    })

                # ✅ Create CRM lead and link the partner
                self.env['crm.lead'].create({
                    'name': record.opportunity_name,
                    'partner_id': partner.id,
                    'email_from': lead_email,
                    'phone': lead_phone,
                    'expected_revenue': record.expected_revenue,
                    'description': record.remark or '',
                })

            submitted_lead_id = record.lead_id.id if record.lead_id else False
            # ✅ Clear lead data after submission
            record.update({
                'lead_id': False,
                'disposition_id': False,
                'searched_lead_id': False,
                'remark': '',
                'dynamic_field_values': '',
                'opportunity_name': '',
                'expected_revenue': 0.0,
            })
            if submitted_lead_id:
                record.pending_callback_lead_ids = [(3, submitted_lead_id)]

    def _fetch_and_store_call_details(self, phone_number):
        config = self.env['ir.config_parameter'].sudo()
        host = config.get_param('external_db.mysql_host')
        user = config.get_param('external_db.mysql_user')
        password = config.get_param('external_db.mysql_password')
        database = config.get_param('external_db.mysql_database')

        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            cursor = conn.cursor(dictionary=True)

            today_date = datetime.today().strftime("%d/%m/%Y")
            phone_number_last10 = phone_number[-10:] if phone_number else ''
            current_user_phone_last10 = (self.env.user.employee_id.mobile_phone or '')[-10:]
            
            cursor.execute("""
                SELECT 
                    Client_Correlation_Id AS client_correlation_id,
                    Customer_Name AS client_name,
                    Caller_Number AS caller_number,
                    Destination_Number AS destination_number,
                    Overall_Call_Status AS overall_call_status,
                    Caller_Operator_Name AS caller_operator_name,
                    Destination_Operator_Name AS destination_operator_name,
                    Call_Type AS call_type,
                    Caller_Circle_Name AS caller_circle,
                    Destination_Circle_Name AS destination_circle,
                    Overall_Call_Duration AS call_duration,
                    Conversation_Duration AS conversation_duration,
                    Date AS call_date,
                    Time AS call_time,
                    Caller_Status AS caller_status,
                    Destination_Status AS destination_status,
                    Hangup_Cause AS hangup_cause,
                    Recording AS recording
                FROM airtel.call_details
                WHERE date = %s
                AND RIGHT(Destination_Number, 10) = %s
            """, (today_date, phone_number_last10))

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            matched = False

            Calldetails = self.env['call.detail.record'].sudo()
            LeadCallMerged = self.env['lead.call.merged'].sudo()

            for row in results:
                caller_number = (row.get('caller_number') or '').lstrip('0')[-10:]
                destination_number = (row.get('destination_number') or '').lstrip('0')[-10:]

                if caller_number == current_user_phone_last10 and destination_number == phone_number_last10:
                    matched = True

                # Combine date and time into datetime
                call_datetime = False
                if row.get('call_date') and row.get('call_time'):
                    try:
                        # Adjust the format according to your database time format
                        time_format = '%H:%M:%S'  # or '%I:%M:%S %p' if using AM/PM
                        call_datetime = datetime.strptime(
                            f"{row['call_date']} {row['call_time']}",
                            "%d/%m/%Y %H:%M:%S"
                        )
                    except ValueError as ve:
                        _logger.warning(f"Could not parse datetime: {ve}")

                client_correlation_id = row.get('client_correlation_id') or False

                # Check if call detail record already exists
                existing_record = Calldetails.search([
                    ('caller_number', '=', caller_number),
                    ('destination_number', '=', destination_number),
                    ('call_datetime', '=', call_datetime),
                    ('client_correlation_id', '=', client_correlation_id),
                ], limit=1)

                if not existing_record:
                    Calldetails.create({
                        'client_name': row.get('client_name'),
                        'caller_number': caller_number,
                        'destination_number': destination_number,
                        'overall_call_status': row.get('overall_call_status'),
                        'caller_operator_name': row.get('caller_operator_name'),
                        'client_correlation_id': client_correlation_id,
                        'destination_operator_name': row.get('destination_operator_name'),
                        'call_type': row.get('call_type'),
                        'caller_circle': row.get('caller_circle'),
                        'destination_circle': row.get('destination_circle'),
                        'call_duration': row.get('call_duration'),
                        'conversation_duration': row.get('conversation_duration'),
                        'call_datetime': call_datetime,  # Using the combined datetime field
                        'caller_status': row.get('caller_status'),
                        'destination_status': row.get('destination_status'),
                        'hangup_cause': row.get('hangup_cause'),
                        'recording': row.get('recording'),
                    })

                # For each record in self (usually wizard / temporary model)
                for record in self:
                    # Check if lead.call.merged record exists
                    existing_merged = LeadCallMerged.search([
                        ('lead_id', '=', record.lead_id.id if record.lead_id else False),
                        ('caller_number', '=', caller_number),
                        ('destination_number', '=', destination_number),
                        ('call_datetime', '=', call_datetime),
                    ], limit=1)

                    if not existing_merged:
                        values = {
                            'lead_id': record.lead_id.id if record.lead_id else False,
                            'user_id': self.env.user.id,
                            'campaign_id': record.lead_id.campaign_id.id if record.lead_id.campaign_id else False,
                            'lead_list_id': record.lead_id.lead_list_id.id if record.lead_id.lead_list_id else False,
                            'disposition_id': record.disposition_id.id if record.disposition_id else False,
                            'remark': record.remark,
                            'client_name': row.get('client_name'),
                            'caller_number': caller_number,
                            'destination_number': destination_number,
                            'client_correlation_id': client_correlation_id,
                            'overall_call_status': row.get('overall_call_status'),
                            'caller_operator_name': row.get('caller_operator_name'),
                            'destination_operator_name': row.get('destination_operator_name'),
                            'call_type': row.get('call_type'),
                            'caller_circle': row.get('caller_circle'),
                            'destination_circle': row.get('destination_circle'),
                            'call_duration': row.get('call_duration'),
                            'conversation_duration': row.get('conversation_duration'),
                            'call_datetime': call_datetime,  # Using the combined datetime field
                            'caller_status': row.get('caller_status'),
                            'destination_status': row.get('destination_status'),
                            'hangup_cause': row.get('hangup_cause'),
                            'recording': row.get('recording'),
                        }
                        if record.disposition_id.is_intrested:
                            values.update({
                                'opportunity_name': record.opportunity_name,
                                'expected_revenue': record.expected_revenue or '',
                            })
                        LeadCallMerged.create(values)

            return matched

        except Exception as e:
            raise ValidationError(f"MySQL connection error: {str(e)}")

    def fetch_next_lead(self, user=None):
        # self.ensure_one()
        if not user:
            raise ValidationError("No user provided.")

        lead_user = self.env['res.users'].sudo().browse(int(user))
        if not lead_user.exists():
            raise ValidationError("User not found.")

        try:
            # Clear any old lead reference
            self.lead_id = False
            lead_user.x_user_lead_id = False

            # Step 1: Get the campaign assigned to the user
            campaign = self.env['campaigns.list'].sudo().search([
                ('user_ids', 'in', lead_user.id)
            ], limit=1)
            if not campaign:
                raise ValidationError("No campaign found for this user.")

            # Step 2: DND list
            dnd_phones = set(self.env['lead.dnd'].sudo().search([]).mapped('phone'))

            # Step 3: Callback lead IDs to skip
            callback_lead_ids = self.env['lead.callback.info'].sudo().search([]).mapped('lead_id.id')

            # Step 4: Get available lead
            domain = [
                ('id', 'not in', callback_lead_ids),
                ('lead_list_id.campaign_id', '=', campaign.id),
                ('x_phone', 'not in', list(dnd_phones)),
                ('is_fetch', '=', False),
                ('lead_list_id.campaign_id.cmp_active', '=', True),
                ('lead_list_id.lead_active', '=', True),
            ]

            order = 'fetch_reset_time asc' if campaign.fetch_lead_as_per_disposition else 'create_date desc'

            lead = self.env['lead.data.lead'].sudo().search(domain, limit=1, order=order)

            if not lead:
                raise UserError("No leads available to assign at the moment.")

            # Mark as fetched
            lead.is_fetch = True
            self.lead_id = lead.id
            lead_user.x_user_lead_id = lead.id
            self.dynamic_field_values = self._prepare_dynamic_field_values(lead)

            _logger.info(f"Lead fetched for user {lead_user.name}: {lead.id}")

        except Exception as e:
            _logger.error(f"Error in fetch_next_lead for user {user}: {str(e)}")
            raise ValidationError("Error fetching next lead. Please contact admin.")

    # def action_fetch_lead(self):
    #     self.ensure_one()
        
    #     user = self.env.user
    #     callback_lead_ids = self.env['lead.callback.info'].search([]).mapped('lead_id.id')
        
    #     # Step 0: Check if a lead is already set in this form and not disposed
    #     if self.lead_id and not self.lead_id.is_fetch:
    #         existing_history = self.env['lead.call.history'].search([
    #             ('user_id', '=', user.id),
    #             ('lead_id', '=', self.lead_id.id),
    #             ('lead_id', 'not in', callback_lead_ids),
    #         ], limit=1)
                        
    #         if not existing_history:
    #             if user.x_user_lead_id.id not in callback_lead_ids:
    #                 raise ValidationError("Please submit the disposition before fetching a new lead.")
        
    #     if user.x_user_lead_id:
    #         existing_history = self.env['lead.call.history'].search([
    #             ('user_id', '=', user.id),
    #             ('lead_id', '=', user.x_user_lead_id.id),
    #             ('lead_id.id', 'not in', callback_lead_ids),
    #         ], limit=1)
    #         if not existing_history:
    #             if user.x_user_lead_id.id not in callback_lead_ids:
    #                 self.lead_id = user.x_user_lead_id
    #                 self.dynamic_field_values = self._prepare_dynamic_field_values(user.x_user_lead_id)
    #                 return
                
    #     # Step 2: Get user's campaign
    #     campaign = self.env['campaigns.list'].search([
    #         ('user_ids', 'in', user.id)
    #     ], limit=1)
        
    #     if not campaign:
    #         raise ValidationError("No campaign found for this user.")
        
    #     # Step 3: Get DND numbers (cache this for better performance)
    #     dnd_phones = set(self.env['lead.dnd'].search([]).mapped('phone'))
        
    #     # Step 4: High-concurrency lead fetching with optimized locking
    #     max_retries = 5
    #     base_delay = 0.05  # 50ms base delay
        
    #     for attempt in range(max_retries):
    #         try:
    #             # Use direct SQL for better performance and atomic operations
    #             lead_id = self._atomic_fetch_lead(campaign, callback_lead_ids, dnd_phones, user)
                
    #             if lead_id:
    #                 lead = self.env['lead.data.lead'].sudo().browse(lead_id)
                    
    #                 # Final verification (should be unnecessary but adds safety)
    #                 if not lead.is_fetch:
    #                     raise ValidationError("Lead fetching failed - please try again.")
                    
    #                 self.lead_id = lead
    #                 user.x_user_lead_id = lead
                    
    #                 print(f"\n\n\nUser {user.id} successfully fetched lead {lead_id}")
                    
    #                 self.dynamic_field_values = self._prepare_dynamic_field_values(lead)
    #                 return
    #             else:
    #                 if attempt < max_retries - 1:
    #                     # Exponential backoff with jitter for better distribution
    #                     delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
    #                     time.sleep(delay)
    #                     continue
    #                 else:
    #                     raise ValidationError("No available leads to assign. Please try again.")
                        
    #         except Exception as e:
    #             if "could not serialize access" in str(e) or "concurrent update" in str(e):
    #                 if attempt < max_retries - 1:
    #                     # Randomized delay to reduce thundering herd effect
    #                     delay = base_delay * (2 ** attempt) + random.uniform(0, 0.2)
    #                     time.sleep(delay)
    #                     continue
    #                 else:
    #                     raise ValidationError("System is busy. Please try again in a moment.")
    #             else:
    #                 raise e

    # def _atomic_fetch_lead(self, campaign, callback_lead_ids, dnd_phones, user):
    #     """
    #     Atomically fetch and lock a lead using optimized SQL
    #     Returns lead_id if successful, None if no leads available
    #     """
        
    #     # Build the base conditions
    #     callback_ids_str = ','.join(map(str, callback_lead_ids)) if callback_lead_ids else '0'
    #     dnd_phones_str = "','".join(dnd_phones) if dnd_phones else ''
        
    #     # Determine ordering
    #     if campaign.fetch_lead_as_per_disposition:
    #         order_clause = "ORDER BY COALESCE(ld.fetch_reset_time, '1970-01-01') ASC, ld.create_date ASC"
    #     else:
    #         order_clause = "ORDER BY ld.create_date DESC"

        
    #     # Use a single atomic SQL query with UPDATE ... RETURNING
    #     # This is the most efficient way to handle high concurrency
    #     query = f"""
    #         UPDATE lead_data_lead 
    #         SET 
    #             is_fetch = true,
    #             fetch_user_id = %s,
    #             fetch_date = %s,
    #             write_date = %s,
    #             write_uid = %s
    #         WHERE id = (
    #             SELECT ld.id 
    #             FROM lead_data_lead ld
    #             INNER JOIN lead_list_data ll ON ld.lead_list_id = ll.id
    #             INNER JOIN campaigns_list cl ON ll.campaign_id = cl.id
    #             WHERE 
    #                 ld.id NOT IN ({callback_ids_str})
    #                 AND ll.campaign_id = %s
    #                 AND ld.is_fetch = false
    #                 AND cl.cmp_active = true
    #                 AND ll.lead_active = true
    #                 {f"AND ld.x_phone NOT IN ('{dnd_phones_str}')" if dnd_phones else ""}
    #             {order_clause}
    #             LIMIT 1
    #             FOR UPDATE SKIP LOCKED
    #         )
    #         RETURNING id;
    #     """
        
    #     params = [
    #         user.id,
    #         fields.Datetime.now(),
    #         fields.Datetime.now(),
    #         user.id,
    #         campaign.id
    #     ]
        
    #     try:
    #         self.env.cr.execute(query, params)
    #         result = self.env.cr.fetchone()
            
    #         if result:
    #             return result[0]
    #         return None
            
    #     except Exception as e:
    #         # Log the error for debugging
    #         print(f"Error in atomic fetch: {e}")
    #         raise e

    # # Alternative method using batch fetching for even better performance
    # def _batch_fetch_leads(self, campaign, callback_lead_ids, dnd_phones, batch_size=50):
    #     """
    #     Pre-fetch a batch of leads and distribute them to users
    #     This can be called periodically to maintain a pool of ready leads
    #     """
        
    #     callback_ids_str = ','.join(map(str, callback_lead_ids)) if callback_lead_ids else '0'
    #     dnd_phones_str = "','".join(dnd_phones) if dnd_phones else ''
        
    #     if campaign.fetch_lead_as_per_disposition:
    #         order_clause = "ORDER BY COALESCE(ld.fetch_reset_time, '1970-01-01') ASC, ld.create_date ASC"
    #     else:
    #         order_clause = "ORDER BY ld.create_date DESC"
        
    #     # Select a batch of leads without locking first
    #     select_query = f"""
    #         SELECT ld.id 
    #         FROM lead_data_lead ld
    #         INNER JOIN lead_list_data ll ON ld.lead_list_id = ll.id
    #         INNER JOIN campaigns_list cl ON ll.campaign_id = cl.id
    #         WHERE 
    #             ld.id NOT IN ({callback_ids_str})
    #             AND ll.campaign_id = %s
    #             AND ld.is_fetch = false
    #             AND cl.cmp_active = true
    #             AND ll.lead_active = true
    #             {f"AND ld.x_phone NOT IN ('{dnd_phones_str}')" if dnd_phones else ""}
    #         {order_clause}
    #         LIMIT %s
    #         FOR UPDATE SKIP LOCKED;
    #     """
        
    #     self.env.cr.execute(select_query, [campaign.id, batch_size])
    #     available_leads = [row[0] for row in self.env.cr.fetchall()]
        
    #     return available_leads

    # # Add this method to your model for monitoring
    # def get_lead_stats(self):
    #     """
    #     Get statistics about lead availability for monitoring
    #     """
    #     query = """
    #         SELECT 
    #             COUNT(*) as total_leads,
    #             COUNT(CASE WHEN is_fetch = false THEN 1 END) as available_leads,
    #             COUNT(CASE WHEN is_fetch = true THEN 1 END) as fetched_leads,
    #             COUNT(CASE WHEN is_fetch = true AND fetch_date > NOW() - INTERVAL '1 hour' THEN 1 END) as recently_fetched
    #         FROM lead_data_lead ld
    #         INNER JOIN lead_list_data ll ON ld.lead_list_id = ll.id
    #         INNER JOIN campaigns_list cl ON ll.campaign_id = cl.id
    #         WHERE cl.cmp_active = true AND ll.lead_active = true;
    #     """
        
    #     self.env.cr.execute(query)
    #     return self.env.cr.dictfetchone()

    def action_fetch_lead(self):
        self.ensure_one()

        user = self.env.user
        print('\n\n\nUserrrrrr',user)
        callback_lead_ids = self.env['lead.callback.info'].search([('user_id', '=', user.id)]).mapped('lead_id.id')
        # # Step 0: Check if a lead is already set in this form and not disposed
        # if self.lead_id and not self.lead_id.is_fetch:
        #     existing_history = self.env['lead.call.history'].search([
        #         ('user_id', '=', user.id),
        #         ('lead_id', '=', self.lead_id.id),
        #         ('lead_id', 'not in', callback_lead_ids),
        #     ], limit=1)
            
        #     if not existing_history:
        #         if user.x_user_lead_id.id not in callback_lead_ids:
        #             raise ValidationError("Please submit the disposition before fetching a new lead.")

        if user.x_user_lead_id:
            existing_history = self.env['lead.call.history'].search([
                ('user_id', '=', user.id),
                ('lead_id', '=', user.x_user_lead_id.id),
                ('lead_id.id', 'not in', callback_lead_ids),
            ], limit=1) 
            if not existing_history:
                # if user.x_user_lead_id.id:
                if user.x_user_lead_id.id not in callback_lead_ids:
                    self.lead_id = user.x_user_lead_id
                    self.dynamic_field_values = self._prepare_dynamic_field_values(user.x_user_lead_id)
                    return
        
        # Step 2: Get user's campaign
        campaign = self.env['campaigns.list'].search([
            ('user_ids', 'in', user.id)
        ], limit=1)

        if not campaign:
            raise ValidationError("No campaign found for this user.")

        # Step 3: Get DND numbers
        dnd_phones = set(self.env['lead.dnd'].search([]).mapped('phone'))
        
        # Step 4: Search for an available lead
        if campaign.fetch_lead_as_per_disposition:
            lead = self.env['lead.data.lead'].sudo().search([
                # ('id', 'not in', callback_lead_ids),
                ('lead_list_id.campaign_id', '=', campaign.id),
                # ('x_phone', 'not in', list(dnd_phones)),
                ('is_fetch', '=', False),
                ('lead_list_id.campaign_id.cmp_active', '=', True),
                ('lead_list_id.lead_active', '=', True),
            ], limit=1, order='fetch_reset_time asc')
        else:
            lead = self.env['lead.data.lead'].sudo().search([
                ('id', 'not in', callback_lead_ids),
                ('lead_list_id.campaign_id', '=', campaign.id),
                # ('x_phone', 'not in', list(dnd_phones)),
                ('is_fetch', '=', False),
                ('lead_list_id.campaign_id.cmp_active', '=', True),
                ('lead_list_id.lead_active', '=', True),
            ], limit=1, order='create_date desc')
        if not lead:
            raise ValidationError("No available leads to assign.")

        if lead.is_fetch:
            raise ValidationError("This lead was just fetched by another user. Try again.") 

        # Step 5: Mark as fetched and assign
        lead.is_fetch = True
        self.lead_id = lead
        user.x_user_lead_id = lead  # ✅ Set it for user for future tabs
        lead.write({
            'is_fetch': True,
            'fetch_user_id': user.id,
            'fetch_date': fields.Datetime.now(),
        })
        print("\n\n\nLeadddddddddddddd",lead)

        self.dynamic_field_values = self._prepare_dynamic_field_values(lead)


        # def action_fetch_lead(self):
        #     self.ensure_one()
        #     user = self.env.user
        #     callback_lead_ids = self.env['lead.callback.info'].search([]).mapped('lead_id.id')

        #     # Step 0: Check if a lead is already set in this form and not disposed
        #     if self.lead_id:
        #         existing_history = self.env['lead.call.history'].search([
        #             ('user_id', '=', user.id),
        #             ('lead_id', '=', self.lead_id.id),
        #             ('lead_id.id', 'not in', callback_lead_ids),
        #         ], limit=1)
        #         if not existing_history:
        #             if user.x_user_lead_id.id not in callback_lead_ids:
        #                 raise ValidationError("Please submit the disposition before fetching a new lead.")

        #     if user.x_user_lead_id:
        #         existing_history = self.env['lead.call.history'].search([
        #             ('user_id', '=', user.id),
        #             ('lead_id', '=', user.x_user_lead_id.id),
        #             ('lead_id.id', 'not in', callback_lead_ids),
        #         ], limit=1)
        #         if not existing_history:
        #             if user.x_user_lead_id.id not in callback_lead_ids:
        #                 self.lead_id = user.x_user_lead_id
        #                 self.dynamic_field_values = self._prepare_dynamic_field_values(user.x_user_lead_id)
        #                 return

        #     # Step 2: Get user's campaign
        #     campaign = self.env['campaigns.list'].search([
        #         ('user_ids', 'in', user.id)
        #     ], limit=1)

        #     if not campaign:
        #         raise ValidationError("No campaign found for this user.")

        #     # Step 3: Get DND numbers
        #     dnd_phones = set(self.env['lead.dnd'].search([]).mapped('phone'))

        #     # Step 4: Find lead safely using SQL lock to avoid double fetch
        #     query = """
        #         SELECT id FROM lead_data_lead
        #         WHERE id NOT IN %s
        #         AND lead_list_id IN (
        #             SELECT id FROM lead_list_data WHERE campaign_id = %s AND lead_active = TRUE
        #         )
        #         AND x_phone NOT IN %s
        #         AND is_fetch = FALSE
        #         ORDER BY {} 
        #         LIMIT 1
        #         FOR UPDATE SKIP LOCKED
        #     """.format('fetch_reset_time asc' if campaign.fetch_lead_as_per_disposition else 'create_date desc')

        #     self.env.cr.execute(query, (
        #         tuple(callback_lead_ids) if callback_lead_ids else (0,),
        #         campaign.id,
        #         tuple(dnd_phones) if dnd_phones else (0,),
        #     ))

        #     lead_row = self.env.cr.fetchone()

        #     if not lead_row:
        #         raise ValidationError("No available leads to assign.")

        #     lead_id = lead_row[0]
        #     lead = self.env['lead.data.lead'].browse(lead_id)

        #     # Step 5: Mark as fetched and assign
        #     lead.is_fetch = True
        #     self.lead_id = lead
        #     user.x_user_lead_id = lead  # Save for user for next time
        #     self.dynamic_field_values = self._prepare_dynamic_field_values(lead)

    def _prepare_dynamic_field_values(self, lead):
        model_fields = self.env['ir.model.fields'].sudo().search([
            ('model', '=', 'lead.data.lead'),
            ('name', 'like', 'x_')
        ])
        label_map = {f.name: f.field_description for f in model_fields}

        dynamic_data = ""
        for field in lead._fields:
            if field.startswith('x_') and hasattr(lead, field):
                value = getattr(lead, field, '')
                if value:
                    label = label_map.get(field, field)
                    dynamic_data += f"{label}: {value}\n"
        return dynamic_data

    def _reopen_form(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'lead.fetch.dailer',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }