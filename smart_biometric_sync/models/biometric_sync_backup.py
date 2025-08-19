import requests
import json
import logging
from datetime import datetime, timedelta
from odoo import models, api, fields, _
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
        _logger.info("Configuration values fetched: API Key=%s, API URL=%s, From Date=%s, To Date=%s", 
                     api_key, api_url, from_date_str, to_date_str)
        if not all([api_key, api_url, from_date_str, to_date_str]):
            _logger.error("Missing configuration values")
            raise UserError(_("Please configure all the required settings in the Attendance Settings."))

        # Convert date strings to datetime objects
        from_date = fields.Date.from_string(from_date_str)
        to_date = fields.Date.from_string(to_date_str)

        # Construct the API URL
        full_api_url = f"{api_url}api/v2/WebAPI/GetDeviceLogs?APIKey={api_key}&FromDate={from_date_str}&ToDate={to_date_str}"
        _logger.info("Constructed API URL: %s", full_api_url)

        # Make the API call
        try:
            response = requests.get(full_api_url)
            if response.status_code == 200:
                data = response.json()
                
                # Print total records in response
                _logger.info(f"Total records in API response: {len(data)}")
                
                # Filter data by date
                filtered_data = self.filter_data_by_date(data, from_date, to_date)
                print(f"Total records after date filtering: {len(filtered_data)}")
                
                # Process the filtered data
                self.process_attendance_data(filtered_data)
            else:
                _logger.error("Failed to fetch data: %s", response.status_code)
                raise UserError(_("Failed to fetch data from the API. Status code: %s") % response.status_code)
        except Exception as e:
            _logger.error("Error fetching attendance data: %s", str(e))
            raise UserError(_("Error fetching attendance data: %s") % str(e))

    def filter_data_by_date(self, data, from_date, to_date):
        """
        Filter the data by the specified date range.
        """
        filtered_data = []
        for record in data:
            log_date_str = record.get('LogDate')
            if log_date_str:
                try:
                    log_date = fields.Date.from_string(log_date_str)
                    if from_date <= log_date <= to_date:
                        filtered_data.append(record)
                except Exception as e:
                    _logger.warning(f"Error parsing date {log_date_str}: {str(e)}")
        return filtered_data

    def process_attendance_data(self, data):
        _logger.info("Processing attendance data")

        matched_records = []
        unmatched_records = []
        
        # Count records by employee code
        employee_records_count = {}
        for record in data:
            emp_code = record.get('EmployeeCode')
            if emp_code:
                if emp_code not in employee_records_count:
                    employee_records_count[emp_code] = 1
                else:
                    employee_records_count[emp_code] += 1

        # Print counts by employee code
        for emp_code, count in employee_records_count.items():
            print(f"Employee Code {emp_code}: {count} records")

        # Fetch all employees from Odoo
        employees = self.env['hr.employee'].search([])
        employee_code_mapping = {}

        # Build a mapping of employee codes to employee records
        for emp in employees:
            if emp.identification_no:
                try:
                    # Extract the numeric part after "SETU - "
                    if "SETU - " in emp.identification_no:
                        code = emp.identification_no.split('-')[-1].strip()
                        if code.isdigit():
                            employee_code_mapping[code] = emp
                        else:
                            _logger.warning(f"Invalid identification_no format for employee {emp.name}: {emp.identification_no}")
                    else:
                        # Try to extract just the numeric part if it exists
                        for part in emp.identification_no.split():
                            if part.isdigit():
                                employee_code_mapping[part] = emp
                                break
                except Exception as e:
                    _logger.warning(f"Error processing identification_no for employee {emp.name}: {str(e)}")
            else:
                _logger.warning(f"Empty identification_no for employee {emp.name}")

        # Process API data
        for record in data:
            employee_code = str(record.get('EmployeeCode'))
            if employee_code in employee_code_mapping:
                matched_records.append((employee_code_mapping[employee_code], record))
            else:
                unmatched_records.append(record)

        # Group by employee
        matched_by_employee = {}
        for emp, rec in matched_records:
            if emp.id not in matched_by_employee:
                matched_by_employee[emp.id] = {"employee": emp, "records": []}
            matched_by_employee[emp.id]["records"].append(rec)
            
        # Sort records for each employee by LogDate
        for emp_id in matched_by_employee:
            matched_by_employee[emp_id]["records"].sort(key=lambda r: r.get('LogDate', ''))
        
        # Create attendance records and print summary for each employee
        attendance_created_count = 0
        for emp_id, data in matched_by_employee.items():
            emp = data["employee"]
            records = data["records"]
            print(f"Employee: {emp.name} (ID: {emp.identification_no})")
            print(f"  Total entries: {len(records)}")
            print(f"  First entry: {records[0].get('LogDate')}")
            
            # Create attendance record
            if len(records) >= 1:
                try:
                    ist_tz = timezone('Asia/Kolkata')

                    # Get first entry for check_in and convert to UTC
                    check_in_str = records[0].get('LogDate')
                    check_in = fields.Datetime.to_datetime(check_in_str)
                    check_in = ist_tz.localize(check_in).astimezone(utc)  # Convert IST to UTC
                    check_in = check_in.replace(tzinfo=None)  # Make datetime naive

                    # Get last entry for check_out if more than one record exists
                    check_out = None
                    if len(records) > 1:
                        check_out_str = records[-1].get('LogDate')
                        check_out = fields.Datetime.to_datetime(check_out_str)
                        check_out = ist_tz.localize(check_out).astimezone(utc)  # Convert IST to UTC
                        check_out = check_out.replace(tzinfo=None)  # Make datetime naive
                        print(f"  Last entry: {check_out_str}")

                    # Check if a record with the same employee_id and check_in already exists
                    existing_record = self.search([
                        ('employee_id', '=', emp.id),
                        ('check_in', '=', check_in),
                    ], limit=1)

                    if existing_record:
                        print(f"  Skipping: Duplicate record already exists for {emp.name} on {check_in}")
                    else:
                        # Create the attendance record
                        attendance_vals = {
                            'employee_id': emp.id,
                            'check_in': check_in,
                        }
                        
                        if check_out:
                            attendance_vals['check_out'] = check_out
                        
                        self.create(attendance_vals)
                        attendance_created_count += 1
                        print(f"  Created attendance record: check_in={check_in}, check_out={check_out or 'None'}")
                
                except Exception as e:
                    print(f"  Error creating attendance record: {str(e)}")
                    _logger.error(f"Error creating attendance record for {emp.name}: {str(e)}")

                    print()

        print("\nUnmatched Records:")
        print(f"Total unmatched records: {len(unmatched_records)}")
        for i, rec in enumerate(unmatched_records[:5]):  # Show just the first 5
            print(f"Record {i+1}: Employee Code = {rec.get('EmployeeCode')}, LogDate = {rec.get('LogDate')}")
        
        if len(unmatched_records) > 5:
            print(f"... and {len(unmatched_records) - 5} more unmatched records")

        # Log the counts
        _logger.info(f"Total records fetched from API: {len(data)}")
        _logger.info(f"Total matched records: {len(matched_records)}")
        _logger.info(f"Total unmatched records: {len(unmatched_records)}")
        _logger.info(f"Total employees with matches: {len(matched_by_employee)}")
        _logger.info(f"Total attendance records created: {attendance_created_count}")

        _logger.info("Attendance data processing completed")