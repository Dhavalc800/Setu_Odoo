import io
import csv
from odoo import http
from odoo.http import request, content_disposition

class ProjectTaskImportController(http.Controller):

    @http.route('/project_task_import/download_sample', type='http', auth="user")
    def download_sample_csv(self, **kwargs):
        """Generate and return a sample CSV file for task import."""
        file_data = io.StringIO()
        writer = csv.writer(file_data)

        # Define the sample CSV headers
        writer.writerow(["Title", "Project", "Sales Order Item", "Schedule Date", "Project Teams", "Tags", "Stage", "Assignee"])
        
        writer.writerow([" "]*8)
        
        file_data.seek(0)
        response = request.make_response(
            file_data.getvalue(),
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', content_disposition('sample_project_tasks.csv'))
            ]
        )
        return response
