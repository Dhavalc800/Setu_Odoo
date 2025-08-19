import requests
import logging
from datetime import datetime
from odoo import models, fields, api
from pytz import timezone, utc
from datetime import datetime, timedelta
from pytz import timezone


_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def send_whatsapp_message(self, employee, message, message_type, half_day=False, full_day=False):
        """Send WhatsApp message and log the history."""
        
        config_params = self.env['ir.config_parameter'].sudo()
        whatsapp_url = config_params.get_param('res.config.settings.whatsapp_url', default='')
        whatsapp_token = config_params.get_param('res.config.settings.whatsapp_token', default='')

        if not whatsapp_url or not whatsapp_token:
            _logger.error("WhatsApp URL or Token is not configured.")
            return

        phone_number = employee.mobile_phone
        if not phone_number:
            _logger.warning(f"Employee {employee.name} has no mobile number set.")
            return

        payload = {
            "token": whatsapp_token,
            "to": phone_number,
            "body": message
        }

        try:
            response = requests.post(whatsapp_url, json=payload)
            if response.status_code == 200:
                _logger.info(f"WhatsApp message sent successfully to {employee.name}.")
            else:
                _logger.error(f"WhatsApp message failed: {response.text}")

            # Log the message in history
            self.env["attandance.msg.history"].create({
                "name": employee.name,
                "employee_id": employee.id,
                "message_date": fields.Date.today(),
                "message_content": message,
                "message_type": message_type,
                "half_day": half_day,
                "full_day": full_day,
            })

        except Exception as e:
            _logger.error(f"WhatsApp message failed for {employee.name}: {str(e)}")


    # def send_whatsapp_message(self, employee, message):
    #     """Send WhatsApp message to the employee using the configured API."""
        
    #     # Fetch WhatsApp credentials from res.config.settings
    #     config_params = self.env['ir.config_parameter'].sudo()
    #     whatsapp_url = config_params.get_param('res.config.settings.whatsapp_url', default='')
    #     whatsapp_token = config_params.get_param('res.config.settings.whatsapp_token', default='')

    #     if not whatsapp_url or not whatsapp_token:
    #         _logger.error("WhatsApp URL or Token is not configured in Res Config Settings.")
    #         return

    #     phone_number = employee.mobile_phone
    #     if not phone_number:
    #         _logger.warning(f"Employee {employee.name} has no mobile number set.")
    #         return

    #     payload = {
    #         "token": whatsapp_token,
    #         "to": phone_number,
    #         "body": message
    #     }

    #     try:
    #         _logger.info(f"Sending WhatsApp message to {phone_number} with payload: {payload}")
    #         response = requests.post(whatsapp_url, json=payload)
            
    #         # Debug API response
    #         _logger.info(f"API Response: {response.status_code}, {response.text}")
    #         if response.status_code == 200:
    #             _logger.info(f"WhatsApp message sent successfully to {employee.name}.")
    #         else:
    #             _logger.error(f"WhatsApp message failed: {response.text}")

    #     except Exception as e:
    #         _logger.error(f"WhatsApp message failed for {employee.name}: {str(e)}")

    @api.model
    def check_late_employees(self):
        """Check employees who haven't checked in by 10:20 AM and send a WhatsApp message based on their check-in status."""
        today = fields.Date.today()
        ist_tz = timezone('Asia/Kolkata')

        # Check if today is Sunday
        if today.strftime('%A') == 'Sunday':
            _logger.info("✅ No messages sent as today is Sunday.")
            return

        # Check if today is a public holiday
        # public_holiday = self.env['resource.calendar.leaves'].search([
        #     ('date_from', '<=', today),
        #     ('date_to', '>=', today),
        # ], limit=1)

        # if public_holiday:
        #     _logger.info(f"✅ No messages sent as today is a public holiday: {public_holiday.name}.")
        #     return

        check_in_deadline = ist_tz.localize(datetime.combine(today, datetime.strptime("09:30", "%H:%M").time())).astimezone(utc)
        warning_time = ist_tz.localize(datetime.combine(today, datetime.strptime("10:20", "%H:%M").time())).astimezone(utc)
        config_params = self.env['ir.config_parameter'].sudo()
        morning_message = config_params.get_param('res.config.settings.morning_message', default='')
        employees = self.env['hr.employee'].search([('attendance_state', '=', 'present')])

        for employee in employees:
            _logger.info(f"Checking employee: {employee.name}")

            last_attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', today)
            ], order="check_in desc", limit=1)

            leave_today = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('request_date_from', '<=', today),
                ('request_date_to', '>=', today),
                ('state', '=', 'validate')
            ], limit=1)

            first_half_leave = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('request_date_from', '=', today),
                ('state', '=', 'validate'),
                ('request_date_from_period', '=', 'am')  # First half leave
            ], limit=1)

            # if last_attendance and last_attendance.check_in:
            #     # Convert check-in time to IST
            #     check_in_time = last_attendance.check_in.replace(tzinfo=utc).astimezone(ist_tz)

            #     _logger.info(f"Employee {employee.name} checked in at {check_in_time.strftime('%I:%M %p')}")

            #     message = f"Dear {employee.name}, you have successfully checked in at {check_in_time.strftime('%I:%M %p')}. Have a great day!"
            #     self.send_whatsapp_message(employee, message)
            if not last_attendance.check_in and employee.is_send_msg and not leave_today and not first_half_leave:
                _logger.warning(f"Employee {employee.name} has not checked in yet.")
                message = morning_message % employee.name
                self.send_whatsapp_message(employee, message, message_type="morning")
                # self.send_whatsapp_message(employee, message)

        _logger.info("Scheduled WhatsApp notifications for morning check-in executed successfully.")

    @api.model
    def check_afternoon_halfday(self):
        """Afternoon Scheduler: Check employees who haven't checked in by 2:00 PM, mark half-day leave, and send a WhatsApp message."""
        today = fields.Date.today()
        ist_tz = timezone('Asia/Kolkata')

        if today.strftime('%A') == 'Sunday':
            _logger.info("✅ No messages sent as today is Sunday.")
            return

        # Check if today is a public holiday
        # public_holiday = self.env['resource.calendar.leaves'].search([
        #     ('date_from', '<=', today),
        #     ('date_to', '>=', today),
        # ], limit=1)

        # if public_holiday:
        #     _logger.info(f"✅ No messages sent as today is a public holiday: {public_holiday.name}.")
        #     return

        halfday_deadline = ist_tz.localize(datetime.combine(today, datetime.strptime("14:00", "%H:%M").time())).astimezone(utc)
        config_params = self.env['ir.config_parameter'].sudo()
        afternoon_message = config_params.get_param('res.config.settings.afternoon_message', default='')
        employees = self.env['hr.employee'].search([('attendance_state', '=', 'present')])

        for employee in employees:
            _logger.info(f"Checking afternoon status for employee: {employee.name}")

            last_attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', today)
            ], order="check_in desc", limit=1)

            leave_today = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('request_date_from', '<=', today),
                ('request_date_to', '>=', today),
                ('state', '=', 'validate')
            ], limit=1)

            first_half_leave = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('request_date_from', '=', today),
                ('state', '=', 'validate'),
                ('request_date_from_period', '=', 'am')
            ], limit=1)
    
            if not last_attendance and employee.is_send_msg and not leave_today and not first_half_leave:
                _logger.warning(f"Employee {employee.name} has not checked in by 2:00 PM. Marking half-day leave.")

                # Send half-day warning message
                message = afternoon_message % employee.name
                # self.send_whatsapp_message(employee, message)
                self.send_whatsapp_message(employee, message, message_type="afternoon", half_day=True)

                # Create half-day leave record
                leave_vals = {
                    'name': 'Auto Half Day Leave',
                    'employee_id': employee.id,
                    'holiday_status_id': self.env.ref('hr_holidays.holiday_status_cl').id,  # Adjust leave type if needed
                    'request_date_from': today,
                    'request_date_to': today,
                    'request_unit_half': True,
                    'state': 'validate',  # Automatically approve
                }
                # leave = self.env['hr.leave'].create(leave_vals)
                # _logger.info(f"Half-day leave created for {employee.name}, Leave ID: {leave.id}")

        _logger.info("Scheduled WhatsApp notifications for afternoon half-day executed successfully.")

    @api.model
    def check_evening_checkout(self):
        """Evening Scheduler: Check employees who haven't checked out by 6:30 PM and send a WhatsApp message."""
        today = fields.Date.today()
        ist_tz = timezone('Asia/Kolkata')

        if today.strftime('%A') == 'Sunday':
            _logger.info("✅ No messages sent as today is Sunday.")
            return

        # Check if today is a public holiday
        # public_holiday = self.env['resource.calendar.leaves'].search([
        #     ('date_from', '<=', today),
        #     ('date_to', '>=', today),
        # ], limit=1)

        # if public_holiday:
        #     _logger.info(f"✅ No messages sent as today is a public holiday: {public_holiday.name}.")
        #     return

        checkout_deadline = ist_tz.localize(datetime.combine(today, datetime.strptime("18:30", "%H:%M").time())).astimezone(utc)
        config_params = self.env['ir.config_parameter'].sudo()
        evening_message = config_params.get_param('res.config.settings.evening_message', default="Dear %s, you have not checked out yet. Please check out soon!")
        half_day_message = config_params.get_param('res.config.settings.half_day_message', default="Dear %s,\n\n⏳ Your total working hours today were less than 6 hours, so your attendance has been marked as Half-Day.\n\n💡 We appreciate your effort and encourage you to complete a full work schedule for better productivity.\n\n🙏 Thank you for your dedication.")
        full_day_message = config_params.get_param('res.config.settings.full_day_message', default="Dear %s,\n\n⚠️ You have worked less than 4 hours today, so your leave has been adjusted to Full-Day Leave.\n\n⏰ To avoid this in the future, please check in on time and complete your working hours.\n\n✅ Your punctuality is valued and appreciated.\n\n🙏 Thank you for your cooperation.")

        employees = self.env['hr.employee'].search([('attendance_state', '=', 'present')])
        for employee in employees:
            _logger.info(f"Checking evening status for employee: {employee.name}")

            last_attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_out', '>=', today)
            ], order="check_out desc", limit=1)
            print("\n\n\nlast_attendance last_attendance",last_attendance)
            leave_today = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('request_date_from', '<=', today),
                ('request_date_to', '>=', today),
                ('state', '=', 'validate')
            ], limit=1)
            print("\n\n\nleave_today leave_today leave_today",leave_today)
            second_half_leave = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('request_date_from', '=', today),
                ('state', '=', 'validate'),
                ('request_date_from_period', '=', 'pm')
            ], limit=1)
            print("\n\n\nsecond_half_leave second_half_leave",second_half_leave)
            # Skip employees who already have leave
            if leave_today or second_half_leave:
                _logger.info(f"Skipping {employee.name} as they are on full-day or second-half leave.")
                continue

            # Determine working hours
            print("\n\n\nTesttttttttttt",last_attendance, last_attendance.check_in)
            if last_attendance and last_attendance.check_in:
                if last_attendance.check_out:
                    worked_hours = (last_attendance.check_out - last_attendance.check_in).total_seconds() / 3600.0
                    _logger.info(f"Employee {employee.name} worked for {worked_hours:.2f} hours.")
                    
                    # **If worked between 4 and 6 hours → Assign Half-Day**
                    if 4 <= worked_hours < 6 and employee.is_send_msg:
                        # self._assign_leave(employee, today, 'half_day')
                        message = half_day_message % employee.name
                        # self.send_whatsapp_message(employee, message)
                        self.send_whatsapp_message(employee, message, message_type="evening", half_day=True)

                    if worked_hours < 4 and employee.is_send_msg:
                        # self._assign_leave(employee, today, 'full_day')
                        message = full_day_message % employee.name
                        # self.send_whatsapp_message(employee, message)
                        self.send_whatsapp_message(employee, message, message_type="evening", full_day=True)

                    # else:
                    #     check_out_time = last_attendance.check_out.replace(tzinfo=utc).astimezone(ist_tz)
                    #     message = f"Dear {employee.name}, you have successfully checked out at {check_out_time.strftime('%I:%M %p')}. Have a great evening!"
                    #     self.send_whatsapp_message(employee, message)
    
                else:
                    if employee.is_send_msg:
                        _logger.warning(f"Employee {employee.name} has not checked out yet.")
                        message = evening_message % employee.name
                        self.send_whatsapp_message(employee, message)
                print("\n\n\nemployee.name employee.name",employee.name)
            else:
                if employee.is_send_msg:
                    print("\n\n\nfull_day_message full_day_message",full_day_message)
                    # self._assign_leave(employee, today, 'full_day')
                    print('\n\n\nemployee.name employee.name',employee.name)
                    message = evening_message % employee.name
                    # self.send_whatsapp_message(employee, message)
                    self.send_whatsapp_message(employee, message, message_type="evening")

        _logger.info("Scheduled WhatsApp notifications for evening check-out executed successfully.")

    def _assign_leave(self, employee, leave_date, leave_type):
        """Assigns a Half-Day or Full-Day leave for the employee."""
        leave_type_id = self.env['hr.leave.type'].search([('name', '=', 'Half Day' if leave_type == 'half_day' else 'Full Day')], limit=1)

        if not leave_type_id:
            _logger.error(f"Leave type '{leave_type}' not found. Cannot assign leave to {employee.name}.")
            return

        leave_vals = {
            'employee_id': employee.id,
            'holiday_status_id': leave_type_id.id,
            'request_date_from': leave_date,
            'request_date_to': leave_date,
            'state': 'validate',
            'request_date_from_period': 'am' if leave_type == 'half_day' else 'full'
        }

        leave = self.env['hr.leave'].create(leave_vals)
        _logger.info(f"Assigned {leave_type} leave to {employee.name} on {leave_date}.")


    @api.model
    def auto_checkout_unchecked_attendance(self):
        """Automatically checks out employees who haven't checked out for past dates (excluding today)."""

        # Get all attendance records where check_out is missing, but NOT for today
        unchecked_attendances = self.env['hr.attendance'].search([
            ('check_out', '=', False),
            ('check_in', '<', fields.Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))  # Exclude today
        ])

        ist_tz = timezone('Asia/Kolkata')  # Adjust based on your timezone

        for attendance in unchecked_attendances:
            check_in_time = attendance.check_in

            # Ensure check-in time is naive before proceeding
            if check_in_time.tzinfo:
                check_in_time = check_in_time.astimezone(utc).replace(tzinfo=None)

            # Set checkout time to 6:30 PM on the same check-in date
            checkout_time_naive = datetime.combine(check_in_time.date(), datetime.strptime("18:30:00", "%H:%M:%S").time())

            # Convert checkout time to UTC (since Odoo stores in UTC)
            checkout_time_utc = ist_tz.localize(checkout_time_naive).astimezone(utc).replace(tzinfo=None)

            # Update the attendance record with check-out time
            attendance.write({
                'check_out': checkout_time_utc
            })

            _logger.info(f"✅ Automatically checked out {attendance.employee_id.name} at {checkout_time_naive.strftime('%I:%M %p')} (IST) for date {check_in_time.date()}.")

        _logger.info("🚀 Scheduled auto-checkout executed successfully.")
