from odoo import models, fields, api
from datetime import datetime, time
import pytz


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_manually_attendance = fields.Boolean(string="Manual Attendance")


    def action_add_checkin(self):
        attendance_model = self.env['hr.attendance']
        leave_model = self.env['hr.leave']
        
        user_tz = pytz.timezone('Asia/Kolkata')
        today = fields.Date.today()

        # Localized 9:30 AM IST -> UTC -> remove tzinfo to make it naive
        local_dt = user_tz.localize(datetime.combine(today, time(hour=9, minute=30)))
        utc_dt = local_dt.astimezone(pytz.utc).replace(tzinfo=None)  # <-- THIS LINE FIXES IT

        for employee in self:
            # Check if employee has approved leave today
            has_leave = leave_model.search_count([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('request_date_from', '<=', today),
                ('request_date_to', '>=', today),
            ])
            if not has_leave:
                attendance_model.create({
                    'employee_id': employee.id,
                    'check_in': utc_dt,
                })

    def action_add_checkout(self):
        attendance_model = self.env['hr.attendance']
        user_tz = pytz.timezone('Asia/Kolkata')
        today = fields.Date.today()

        # Set 6:00 PM IST (checkout time), convert to UTC, then remove tz
        local_dt = user_tz.localize(datetime.combine(today, time(hour=18, minute=30)))
        utc_dt = local_dt.astimezone(pytz.utc).replace(tzinfo=None)

        for employee in self:
            # Get latest check-in for today
            attendance = attendance_model.search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', datetime.combine(today, time.min)),
                ('check_in', '<=', datetime.combine(today, time.max)),
                ('check_out', '=', False),
            ], limit=1, order="check_in desc")

            if attendance:
                attendance.check_out = utc_dt