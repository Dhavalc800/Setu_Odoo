from odoo import models, fields, api
from datetime import datetime
import mysql.connector
from odoo.exceptions import UserError

class PysicalMeeting(models.Model):
    _name = 'pysical.meeting'
    _description = 'Pysical Meeting'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char("Name", required=True, tracking=True)
    email = fields.Char("Email", tracking=True)
    contact = fields.Char("Contact", tracking=True)
    slab = fields.Char("Slab", tracking=True)
    state = fields.Char("State", tracking=True)
    pincode = fields.Char("Pin Code", tracking=True)
    type = fields.Char("Type", tracking=True)
    district = fields.Char("District", tracking=True)
    user_id = fields.Many2one('res.users', string="Assign User", tracking=True)
    meeting_date = fields.Datetime("Meeting Date", tracking=True)
    disposition = fields.Char("Disposition", tracking=True)
    meeting_user_id = fields.Many2one('res.users', string="Meeting Person", tracking=True)
    
    client_name = fields.Char("Client Name", readonly=True, tracking=True)
    caller_number = fields.Char("Caller Number", readonly=True, tracking=True)
    destination_number = fields.Char("Destination Number", readonly=True, tracking=True)
    overall_call_status = fields.Char("Overall Call Status", readonly=True, tracking=True)
    caller_operator_name = fields.Char("Caller Operator", readonly=True, tracking=True)
    client_correlation_id = fields.Char("Call ID", readonly=True, tracking=True)
    destination_operator_name = fields.Char("Destination Operator", readonly=True, tracking=True)
    call_type = fields.Char("Call Type", readonly=True, tracking=True)
    caller_circle = fields.Char("Caller Circle", readonly=True, tracking=True)
    destination_circle = fields.Char("Destination Circle", readonly=True, tracking=True)
    call_duration = fields.Char("Call Duration", readonly=True, tracking=True)
    conversation_duration = fields.Char("Conversation Duration", readonly=True, tracking=True)
    call_datetime = fields.Datetime("Call Datetime", readonly=True, tracking=True)
    caller_status = fields.Char("Caller Status", readonly=True, tracking=True)
    destination_status = fields.Char("Destination Status", readonly=True, tracking=True)
    hangup_cause = fields.Char("Hangup Cause", readonly=True, tracking=True)
    recording = fields.Char("Recording Path", readonly=True, tracking=True)

    approved_by = fields.Many2one('res.users', string="Updated By", tracking=True)
    bdm_branch = fields.Many2one(
        'employee.branch', string="BDM Branch",
        store=True, readonly=True, tracking=True, compute="_compute_bdm_branch"
    )
    stage_by_bdm = fields.Selection([
        ('approve_bdm', 'Approved By BDM'),
        ('not_approve_bdm', 'Not Approve By BDM'),
    ], string='Stage By BDM', default=False, tracking=True)

    stage_by_admin = fields.Selection([
        ('approve', 'Approved'),
        ('not_approve', 'Not Approved'),
    ], string='Stage By Admin', default=False, tracking=True)

    bdm_approved_on = fields.Datetime(
        string="BDM Approved On", tracking=True, readonly=True
    )
    approved_on = fields.Datetime(
        string="Approved On", tracking=True, readonly=True
    )

    @api.depends('user_id')
    def _compute_bdm_branch(self):
        for record in self:
            employee = record.user_id.employee_id if record.user_id else False
            record.bdm_branch = employee.branch_id.id if employee else False

    @api.model
    def create(self, vals):
        if 'stage_by_bdm' in vals:
            vals['bdm_approved_on'] = fields.Datetime.now()
            vals['approved_by'] = self.env.uid
        if 'stage_by_admin' in vals:
            vals['approved_on'] = fields.Datetime.now()
            vals['approved_by'] = self.env.uid
        return super().create(vals)

    def write(self, vals):
        if 'stage_by_bdm' in vals:
            vals['bdm_approved_on'] = fields.Datetime.now()
            vals['approved_by'] = self.env.uid
        if 'stage_by_admin' in vals:
            vals['approved_on'] = fields.Datetime.now()
            vals['approved_by'] = self.env.uid
        return super().write(vals)

    def action_fetch_call_data(self):
        for record in self:
            phone_number = record.contact
            if not phone_number:
                raise UserError("Please enter a contact number before fetching call data.")

            employee_mobile = record.meeting_user_id.employee_id.mobile_phone
            if not employee_mobile:
                raise UserError("Meeting user's mobile number is not set in Employee profile.")

            # Get config
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
                today = datetime.today().strftime("%d/%m/%Y")
                phone_last10 = phone_number[-10:]
                emp_mobile_last10 = employee_mobile[-10:]

                query = """
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
                    WHERE Date = %s
                    AND RIGHT(Destination_Number, 10) = %s
                    AND RIGHT(Caller_Number, 10) = %s
                    ORDER BY Time DESC
                    LIMIT 1
                """
                cursor.execute(query, (today, phone_last10, emp_mobile_last10))
                row = cursor.fetchone()

                if row:
                    # Double-check match to avoid false positives
                    dest_last10 = row.get('destination_number', '')[-10:]
                    caller_last10 = row.get('caller_number', '')[-10:]
                    if dest_last10 == phone_last10 and caller_last10 == emp_mobile_last10:
                        call_datetime = datetime.strptime(f"{row['call_date']} {row['call_time']}", "%d/%m/%Y %H:%M:%S")
                        record.write({
                            'client_name': row.get('client_name'),
                            'caller_number': row.get('caller_number'),
                            'destination_number': row.get('destination_number'),
                            'overall_call_status': row.get('overall_call_status'),
                            'caller_operator_name': row.get('caller_operator_name'),
                            'client_correlation_id': row.get('client_correlation_id'),
                            'destination_operator_name': row.get('destination_operator_name'),
                            'call_type': row.get('call_type'),
                            'caller_circle': row.get('caller_circle'),
                            'destination_circle': row.get('destination_circle'),
                            'call_duration': row.get('call_duration'),
                            'conversation_duration': row.get('conversation_duration'),
                            'call_datetime': call_datetime,
                            'caller_status': row.get('caller_status'),
                            'destination_status': row.get('destination_status'),
                            'hangup_cause': row.get('hangup_cause'),
                            'recording': row.get('recording'),
                        })
                    else:
                        raise UserError("Call data found, but does not match both contact and meeting user's number.")
                else:
                    raise UserError("No call data found for this number and user today.")

                cursor.close()
                conn.close()

            except mysql.connector.Error as err:
                raise UserError(f"MySQL Error: {err}")

    def action_pysical_meeting_wizard(self):
        """ Open wizard with selected assignments """
        return {
            'name': 'Assign pysical Meeting to User',
            'type': 'ir.actions.act_window',
            'res_model': 'pysical.meeting.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_assignment_ids': [(6, 0, self.ids)],
                'active_ids': self.ids,
                'active_model': 'pysical.meeting.wizard',
            },
        }