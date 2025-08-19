from odoo import http
from odoo.http import request
import csv
import io
import xlwt

class LeadListDownloadController(http.Controller):

    @http.route('/lead_list/<int:record_id>/download_csv', type='http', auth='user')
    def download_csv(self, record_id):
        record = request.env['lead.list.data'].sudo().browse(record_id)
        if not record.exists():
            return request.not_found()

        # Get selected report column field names
        column_fields = record.report_column_ids.mapped('name')

        # Prepare CSV content
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header row
        writer.writerow(column_fields)

        # Write one data row based on current record's field values
        row = []
        for field in column_fields:
            val = record[field]
            if isinstance(val, models.BaseModel):
                row.append(val.display_name)
            else:
                row.append(val or '')
        writer.writerow(row)

        output.seek(0)
        csv_content = output.read()
        output.close()

        return request.make_response(
            csv_content,
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', 'attachment; filename="lead_list_data.csv"')
            ]
        )
    
    @http.route('/lean/manual/lead/download_format', type='http', auth='user')
    def download_format(self, **kwargs):
        headers = [
            'employee_id', 'company_name', 'email', 'bdm', 'service', 'slab', 'source', 'state', 'phone', 'remark'
        ]
        
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(headers)
        csv_content = buffer.getvalue()
        buffer.close()

        return request.make_response(
            csv_content,
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', 'attachment; filename="manual_lead_format.csv"')
            ]
        )

    @http.route('/lead/download_format', type='http', auth='user')
    def download_csv_format(self, **kwargs):
        headers = [
            'employee_id', 'name', 'dispostion_id', 'datetime', 'date', 'time_slot', 'email',
            'phone', 'slab', 'service', 'source', 'type', 'city',
            'lead_type', 'sale_person_name', 'remarks'
        ]

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(headers)
        csv_content = buffer.getvalue()
        buffer.close()

        return request.make_response(
            csv_content,
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', 'attachment; filename="lead_format.csv"')
            ]
        )

    @http.route('/hbad/download_sample', type='http', auth='user')
    def download_hbad_sample(self, **kwargs):
        headers = [
            'Date', 'Booking ID', 'Allocation Date', 'Contact Number', 'Customer Name',
            'Structure', 'Products', 'Location', 'Status', 'Remarks', 'Brief'
        ]

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(headers)
        # sample_row = [
        #     '01/03/2025', 'BK001', '05/03/2025', '9876543210', 'John Doe',
        #     'Private Limited', 'Startup India,Grants', 'Ahmedabad', 'Active',
        #     'Initial discussion', 'Details about the services discussed.'
        # ]
        # writer.writerow(sample_row)

        csv_content = buffer.getvalue()
        buffer.close()

        return request.make_response(
            csv_content,
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', 'attachment; filename="hbad_sample.csv"')
            ]
        )

    @http.route('/lead/download_format_xls', type='http', auth='user')
    def download_xls_format(self, **kwargs):
        headers = [
            'employee_id', 'name', 'dispostion_id', 'datetime', 'date', 'time_slot', 'email',
            'phone', 'slab', 'service', 'source', 'type', 'city',
            'lead_type', 'sale_person_name', 'remarks'
        ]


        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Format')

        for col, header in enumerate(headers):
            sheet.write(0, col, header)

        stream = io.BytesIO()
        workbook.save(stream)
        xls_content = stream.getvalue()

        return request.make_response(
            xls_content,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename="lead_format.xls"')
            ]
        )