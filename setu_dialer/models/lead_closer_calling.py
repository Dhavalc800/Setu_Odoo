from odoo import models, fields, api
import mysql.connector
from datetime import datetime
from odoo.exceptions import ValidationError


class LeadCloserCalling(models.Model):
    _name = 'lead.closer.calling'
    _description = 'Lead Closer Calling'
    _rec_name = "lead_id"
    _order = "create_date desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Lead Info
    employee_id = fields.Many2one('closer.name', string="Assigned To")
    user_id = fields.Many2one('res.users', string="Assigned By", default=lambda self: self.env.user)
    lead_id = fields.Many2one('lead.data.lead', string='Lead')
    closer_user_id = fields.Many2one('res.users', string="Closer User ID")
    company_name = fields.Char(string="Company Name")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    state = fields.Char(string="State")
    source = fields.Char(string="Source")
    service = fields.Char(string="Service")
    bdm_id = fields.Many2one('res.users', string="BDM")
    slab = fields.Char(string="Slab")
    
    # Lead Disposition
    dynamic_summary = fields.Text(string="Dynamic Summary", readonly=True)
    disposition_id = fields.Many2one('dispo.list.name', string="Disposition")
    remark = fields.Text(string="Remark")
    interested = fields.Boolean(compute="_compute_interested", string="Interested", store=True)
    opportunity_name = fields.Char(string="Opportunity")
    expected_revenue = fields.Float(string="Expected Revenue")
    call_back_date = fields.Datetime(string="Call Back Date")
    is_callback = fields.Boolean(
        string="Is Call Back",
        related='disposition_id.is_callback',
        store=True,
        readonly=True
    )

    # Call Details
    client_name = fields.Char(string="Client Name")
    caller_number = fields.Char(string="Caller Number")
    destination_number = fields.Char(string="Destination Number")
    call_status = fields.Char(string="Overall Call Status")
    caller_operator = fields.Char(string="Caller Operator Name")
    destination_operator = fields.Char(string="Destination Operator Name")
    call_type = fields.Char(string="Call Type")
    caller_circle = fields.Char(string="Caller Circle")
    destination_circle = fields.Char(string="Destination Circle")
    call_duration = fields.Char(string="Call Duration")
    conversation_duration = fields.Char(string="Conversation Duration")
    call_date = fields.Datetime(string="Call Date")
    caller_status = fields.Char(string="Caller Status")
    destination_status = fields.Char(string="Destination Status")
    hangup_cause = fields.Char(string="Hangup Cause")
    recording_path = fields.Char(string="Recording Path")

    def write(self, vals):
        disposition_changed = 'disposition_id' in vals
        phone_present = self.phone or vals.get('phone')
        result = super(LeadCloserCalling, self).write(vals)
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
                    Overall_Call_Status AS call_status,
                    Caller_Operator_Name AS caller_operator,
                    Destination_Operator_Name AS destination_operator,
                    Call_Type AS call_type,
                    Caller_Circle_Name AS caller_circle,
                    Destination_Circle_Name AS destination_circle,
                    Overall_Call_Duration AS call_duration,
                    Conversation_Duration AS conversation_duration,
                    Date AS call_date,
                    Caller_Status AS caller_status,
                    Destination_Status AS destination_status,
                    Hangup_Cause AS hangup_cause,
                    Recording AS recording_path
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
                    self.write({
                        'client_name': row.get('client_name'),
                        'caller_number': caller_number,
                        'destination_number': destination_number,
                        'call_status': row.get('call_status'),
                        'caller_operator': row.get('caller_operator'),
                        'destination_operator': row.get('destination_operator'),
                        'call_type': row.get('call_type'),
                        'caller_circle': row.get('caller_circle'),
                        'destination_circle': row.get('destination_circle'),
                        'call_duration': row.get('call_duration'),
                        'conversation_duration': row.get('conversation_duration'),
                        'call_date': datetime.strptime(row.get('call_date'), "%d/%m/%Y") if row.get('call_date') else False,
                        'caller_status': row.get('caller_status'),
                        'destination_status': row.get('destination_status'),
                        'hangup_cause': row.get('hangup_cause'),
                        'recording_path': row.get('recording_path')
                    })

        except Exception as e:
            raise ValidationError(f"MySQL connection error: {str(e)}")

    @api.depends('disposition_id')
    def _compute_interested(self):
        for rec in self:
            rec.interested = rec.disposition_id.is_intrested if rec.disposition_id else False
            print("Computed interested status: %s for record %s", rec.interested, rec.id)

    def action_create_opportunity(self):
        for lead in self:
            if lead.interested:
                partner = self.env['res.partner'].search([
                    ('name', '=', lead.company_name)
                ], limit=1)

                if not partner:
                    partner = self.env['res.partner'].create({
                        'name': lead.company_name,
                        'phone': lead.phone,
                        'email': lead.email,
                    })
                
                self.env['crm.lead'].create({
                    'name': lead.opportunity_name or lead.company_name,
                    'partner_id': partner.id,
                    'phone': lead.phone,
                    'email_from': lead.email,
                    'user_id': self.env.uid,
                    'expected_revenue': lead.expected_revenue,
                    'description': f"Slab: {lead.slab}\nSource: {lead.source}\nService: {lead.service}\nState: {lead.state}\nRemark: {lead.remark}",
                })

# from odoo import models, fields

# class LeadCloserCalling(models.Model):
#     _name = 'lead.closer.calling'
#     _description = 'Lead Closer Calling'

#     # Lead Info
#     employee_id = fields.Many2one('hr.employee', string="Employee")
#     user_id = fields.Many2one('res.users', string="Administrator", default=lambda self: self.env.user)
#     company_name = fields.Char(string="Company Name")
#     email = fields.Char(string="Email")
#     phone = fields.Char(string="Phone")
#     state = fields.Char(string="State")
#     source = fields.Char(string="Source")
#     service = fields.Char(string="Service")
#     bdm_id = fields.Many2one('res.users', string="BDM")
#     slab = fields.Char(string="Slab")

#     # Lead Disposition
#     dynamic_summary = fields.Text(string="Dynamic Summary")
#     disposition_id = fields.Many2one('dispo.list.name', string="Disposition")
#     remark = fields.Text(string="Remark")

#     # Call Details
#     client_name = fields.Char(string="Client Name")
#     caller_number = fields.Char(string="Caller Number")
#     destination_number = fields.Char(string="Destination Number")
#     call_status = fields.Char(string="Overall Call Status")
#     caller_operator = fields.Char(string="Caller Operator Name")
#     destination_operator = fields.Char(string="Destination Operator Name")
#     call_type = fields.Char(string="Call Type")
#     caller_circle = fields.Char(string="Caller Circle")
#     destination_circle = fields.Char(string="Destination Circle")
#     call_duration = fields.Char(string="Call Duration")
#     conversation_duration = fields.Char(string="Conversation Duration")
#     call_date = fields.Datetime(string="Call Date")
#     caller_status = fields.Char(string="Caller Status")
#     destination_status = fields.Char(string="Destination Status")
#     hangup_cause = fields.Char(string="Hangup Cause")
#     recording_path = fields.Char(string="Recording Path")
