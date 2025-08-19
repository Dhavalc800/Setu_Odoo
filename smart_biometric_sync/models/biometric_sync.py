import requests
import json
import logging
from datetime import datetime, timedelta
from odoo import models, fields, _
from odoo.exceptions import UserError
from pytz import timezone, utc
_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def fetch_attendance_data(self):
        _logger.info("Fetching attendance data started")
        config_params = self.env['ir.config_parameter'].sudo()
        api_key = config_params.get_param('hr_attendance.api_key')
        api_url = config_params.get_param('hr_attendance.api_url')
        from_date_str = config_params.get_param('hr_attendance.from_date')
        to_date_str = config_params.get_param('hr_attendance.to_date')
        if not all([api_key, api_url, from_date_str, to_date_str]):
            raise UserError(_("Please configure all required settings in Attendance Settings."))

        from_date = fields.Date.from_string(from_date_str)
        to_date = fields.Date.from_string(to_date_str)

        full_api_url = f"{api_url}api/v2/WebAPI/GetDeviceLogs?APIKey={api_key}&FromDate={from_date_str}&ToDate={to_date_str}"
        _logger.info("Constructed API URL: %s", full_api_url)
        try:
            response = requests.get(full_api_url)
            if response.status_code == 200:
                data = response.json()
                filtered_data = self.filter_data_by_date(data, from_date, to_date)
                self.process_attendance_data(filtered_data)
            else:
                raise UserError(_("Failed to fetch data from API. Status code: %s") % response.status_code)
        except Exception as e:
            _logger.error("Error fetching attendance data: %s", str(e))
            raise UserError(_("Error fetching attendance data: %s") % str(e))

    def filter_data_by_date(self, data, from_date, to_date):
        """Filter logs based on date range."""
        filtered_data = []
        for record in data:
            try:
                log_datetime = fields.Datetime.to_datetime(record.get('LogDate'))
                log_date = log_datetime.date()
                if from_date <= log_date <= to_date:
                    filtered_data.append(record)
            except Exception as e:
                _logger.warning(f"Error parsing date {record.get('LogDate')}: {str(e)}")
        return filtered_data

    def process_attendance_data(self, data):
        """Process attendance data and create/update records properly."""
        _logger.info("Processing attendance data")

        # Fetch all employees and map them by identification number
        employees = self.env['hr.employee'].search([])
        employee_code_mapping = {str(emp.identification_no.split('-')[-1].strip()): emp for emp in employees if emp.identification_no}

        attendance_grouped = {}

        # Group logs by employee and date
        for record in data:
            emp_code = str(record.get('EmployeeCode'))
            log_datetime = fields.Datetime.to_datetime(record.get('LogDate'))

            if emp_code in employee_code_mapping:
                emp = employee_code_mapping[emp_code]
                log_date = log_datetime.date()

                if emp.id not in attendance_grouped:
                    attendance_grouped[emp.id] = {}

                if log_date not in attendance_grouped[emp.id]:
                    attendance_grouped[emp.id][log_date] = []

                attendance_grouped[emp.id][log_date].append(log_datetime)

        # Process each employee's logs per day
        attendance_created_count = 0
        for emp_id, dates in attendance_grouped.items():
            emp = self.env['hr.employee'].browse(emp_id)
            ist_tz = timezone('Asia/Kolkata')

            last_check_out = None  # Track last check-out per employee

            for log_date, log_times in sorted(dates.items()):
                log_times.sort()
                check_in = log_times[0]
                check_out = log_times[-1] if len(log_times) > 1 else None

                # Convert to UTC before storing
                check_in = ist_tz.localize(check_in).astimezone(utc).replace(tzinfo=None)
                if check_out:
                    check_out = ist_tz.localize(check_out).astimezone(utc).replace(tzinfo=None)

                # Check if an attendance record already exists for this employee and date
                existing_attendance = self.env['hr.attendance'].search([
                    ('employee_id', '=', emp.id),
                    ('check_in', '>=', check_in),
                    ('check_in', '<', check_in + timedelta(days=1))
                ], limit=1)

                if existing_attendance:
                    # If check-out is missing in the existing record, update it
                    if check_out and not existing_attendance.check_out:
                        existing_attendance.write({'check_out': check_out})
                        _logger.info(f"Updated check-out for {emp.name} on {log_date}")
                else:
                    # If check-in or check-out is missing, set check-out to check-in + 1 minute
                    today_date = fields.Date.today()
                    if not check_out:
                        if log_date == today_date:
                            _logger.info(f"Skipping check-out for {emp.name} on {log_date} as they are still in office.")
                            check_out = None
                        else:
                            check_out = check_in + timedelta(minutes=1)
                            _logger.warning(f"Added automatic check-out for {emp.name} on {log_date} (1 minute after check-in).")

                    # Skip if check-in is before the last check-out
                    if last_check_out and check_in < last_check_out:
                        _logger.warning(f"Skipping invalid check-in for {emp.name} on {log_date} (before last check-out).")
                        continue

                    # Create new attendance record
                    attendance_vals = {
                        'employee_id': emp.id,
                        'check_in': check_in,
                        'check_out': check_out,
                    }
                    self.env['hr.attendance'].create(attendance_vals)
                    attendance_created_count += 1
                    _logger.info(f"Created new attendance for {emp.name} on {log_date}")

                # Update last_check_out
                if check_out:
                    last_check_out = check_out

        _logger.info(f"Total attendance records created: {attendance_created_count}")
