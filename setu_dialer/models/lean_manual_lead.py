from odoo import models, fields, api
import mysql.connector
from datetime import datetime
from odoo.exceptions import ValidationError


class LeanManualLead(models.Model):
    _name = 'lean.manual.lead'
    _description = 'Manual Lead Entry'
    _rec_name = "company_name"
    _order = "create_date desc"

    employee_id = fields.Many2one('res.users', string="Employee", default=lambda self: self.env.user)
    company_name = fields.Char(string="Company Name")
    email = fields.Char(string="email")
    slab = fields.Char(string="Slab")
    bdm = fields.Char(string="BDM")
    phone = fields.Char(string="Phone")
    source = fields.Char(string="Source")
    service = fields.Char(string="Service")
    state = fields.Char(string="State")
    remark = fields.Text(string="Remark")
    disposition_id = fields.Many2one('dispo.list.name', string="Disposition")
    interested = fields.Boolean(compute="_compute_interested", string="Interested", store=True)
    opportunity_name = fields.Char(string="Opportunity")
    expected_revenue = fields.Float(string="Expected Revenue")
    call_back_date = fields.Datetime(string="Call Back Date")

    dynamic_field_values = fields.Text(string="Lead Data", readonly=True)
    dynamic_summary = fields.Text(string="Dynamic Summary", readonly=True)

    is_callback = fields.Boolean(
        string="Is Call Back",
        related='disposition_id.is_callback',
        store=True,
        readonly=True
    )
    # wizard_id = fields.Many2one('lead.transfer.wizard', string="Wizard Ref", ondelete='set null')

    # Inside lean.manual.lead
    client_name = fields.Char(string="Client Name")
    caller_number = fields.Char(string="Caller Number")
    destination_number = fields.Char(string="Destination Number")
    overall_call_status = fields.Char(string="Overall Call Status")
    caller_operator_name = fields.Char(string="Caller Operator Name")
    destination_operator_name = fields.Char(string="Destination Operator Name")
    call_type = fields.Char(string="Call Type")
    caller_circle = fields.Char(string="Caller Circle")
    destination_circle = fields.Char(string="Destination Circle")
    call_duration = fields.Char(string="Call Duration")
    conversation_duration = fields.Char(string="Conversation Duration")
    call_date = fields.Date(string="Call Date")
    caller_status = fields.Char(string="Caller Status")
    destination_status = fields.Char(string="Destination Status")
    hangup_cause = fields.Char(string="Hangup Cause")
    recording = fields.Char(string="Recording Path")

    # def write(self, vals):
    #     disposition_changed = 'disposition_id' in vals
    #     phone_present = self.phone or vals.get('phone')
    #     result = super(LeanManualLead, self).write(vals)

    #     if result and disposition_changed:
    #         for rec in self:
    #             # 1. Fetch updated disposition
    #             disposition = rec.disposition_id

    #             # 2. Create a queue record
    #             self.env['disposition.queue'].create({
    #                 'lead_id': None,  # Assuming manual lead is not linked to lead.data.lead
    #                 'campaign_id': None,  # Fill if campaign_id is available
    #                 'lead_list_id': None,  # Fill if lead_list_id is available
    #                 'disposition_id': disposition.id,
    #                 'call_by': rec.employee_id.id,
    #                 'disposition_time': fields.Datetime.now(),
    #                 'disposition_from': 'Manual Lead',
    #             })

    #             # 3. Optionally fetch call details
    #             if phone_present:
    #                 rec._fetch_and_store_call_details()

    #     return result


    def write(self, vals):
        disposition_changed = 'disposition_id' in vals
        phone_present = self.phone or vals.get('phone')
        result = super(LeanManualLead, self).write(vals)
        if disposition_changed and phone_present:
            for rec in self:
                rec._fetch_and_store_call_details()
        return result

    def _fetch_and_store_call_details(self):
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
            phone_number_last10 = (self.phone or '')[-10:]
            current_user_phone_last10 = (self.env.user.employee_id.mobile_phone or '')[-10:]

            cursor.execute("""
                SELECT 
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

            for row in results:
                caller_number = (row.get('caller_number') or '').lstrip('0')[-10:]
                destination_number = (row.get('destination_number') or '').lstrip('0')[-10:]
                if caller_number == current_user_phone_last10 and destination_number == phone_number_last10:
                    self.client_name = row.get('client_name')
                    self.caller_number = caller_number
                    self.destination_number = destination_number
                    self.overall_call_status = row.get('overall_call_status')
                    self.caller_operator_name = row.get('caller_operator_name')
                    self.destination_operator_name = row.get('destination_operator_name')
                    self.call_type = row.get('call_type')
                    self.caller_circle = row.get('caller_circle')
                    self.destination_circle = row.get('destination_circle')
                    self.call_duration = row.get('call_duration')
                    self.conversation_duration = row.get('conversation_duration')
                    self.call_date = datetime.strptime(row.get('call_date'), "%d/%m/%Y").date() if row.get('call_date') else False
                    self.caller_status = row.get('caller_status')
                    self.destination_status = row.get('destination_status')
                    self.hangup_cause = row.get('hangup_cause')
                    self.recording = row.get('recording')

        except Exception as e:
            raise ValidationError(f"MySQL connection error: {str(e)}")

    @api.depends('disposition_id')
    def _compute_interested(self):
        for rec in self:
            rec.interested = rec.disposition_id.name.lower() == 'interested' if rec.disposition_id else False

    def action_create_opportunity(self):
        for lead in self:
            if lead.interested:
                partner = self.env['res.partner'].search([
                    ('name', '=', lead.company_name)
                    ], limit=1)

                # If partner does not exist, create it
                if not partner:
                    partner = self.env['res.partner'].create({
                        'name': lead.company_name,
                        'phone': lead.phone,
                    })
                
                self.env['crm.lead'].create({
                    'name': lead.opportunity_name or lead.company_name,
                    'partner_id': partner.id,
                    'phone': lead.phone,
                    'user_id': lead.employee_id.id,
                    'expected_revenue': lead.expected_revenue,
                    'description': f"Slab: {lead.slab}\nSource: {lead.source}\nState: {lead.state}\nRemark: {lead.remark}",
                })