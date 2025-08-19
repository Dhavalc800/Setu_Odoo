from odoo import models, fields, api, _
from odoo.exceptions import UserError
import io
import xlsxwriter
import base64
import logging
import time
from datetime import datetime
import gc

_logger = logging.getLogger(__name__)


class MassiveTaskExportWizard(models.TransientModel):
    _name = 'massive.task.export.wizard'
    _description = 'Wizard for Massive Task Export (100K+ records)'

    file_data = fields.Binary('File')
    file_name = fields.Char('Filename', default='massive_tasks.xlsx')
    batch_size = fields.Integer('Batch Size', default=10000, 
                               help="Number of records to process in each batch")
    max_records = fields.Integer('Max Records', default=0,
                                help="Maximum records to export (0 = all)")
    
    # Progress tracking
    total_records = fields.Integer('Total Records', readonly=True)
    processed_records = fields.Integer('Processed Records', readonly=True)
    progress_percentage = fields.Float('Progress %', readonly=True)
    status = fields.Selection([
        ('ready', 'Ready'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error')
    ], default='ready', readonly=True)

    def _get_task_count(self):
        """Get total task count"""
        return self.env['project.task'].search_count([])

    def _process_super_chunk(self, task_ids):
        """Process very large chunks with minimal memory usage"""
        processed_data = []
        
        # Use direct SQL for maximum performance
        query = """
        SELECT 
            pt.id,
            pt.name,
            COALESCE(rp.name, '') as customer_name,
            COALESCE(pp.name, '') as project_name,
            COALESCE(ps.name, '') as stage_name,
            COALESCE(ru.name, '') as created_by_name,
            pt.create_date::text as created_on
        FROM project_task pt
        LEFT JOIN res_partner rp ON pt.partner_id = rp.id
        LEFT JOIN project_project pp ON pt.project_id = pp.id
        LEFT JOIN project_task_stage ps ON pt.stage_id = ps.id
        LEFT JOIN res_users ru ON pt.create_uid = ru.id
        WHERE pt.id = ANY(%s)
        ORDER BY pt.id
        """
        
        self.env.cr.execute(query, (list(task_ids.ids),))
        results = self.env.cr.fetchall()
        
        for row in results:
            # Get assignees separately
            assignees = []
            try:
                assignee_query = """
                SELECT ru.name 
                FROM res_users ru
                JOIN project_task_user_rel ptur ON ru.id = ptur.user_id
                WHERE ptur.task_id = %s
                """
                self.env.cr.execute(assignee_query, (row[0],))
                assignee_results = self.env.cr.fetchall()
                assignees = [a[0] for a in assignee_results if a[0]]
            except:
                pass
            
            processed_data.append({
                'task_id': row[0],
                'task_name': row[1] or '',
                'customer': row[2] or '',
                'project': row[3] or '',
                'stage': row[4] or '',
                'created_by': row[5] or '',
                'created_on': row[6] or '',
                'assignees': ', '.join(assignees) if assignees else ''
            })
        
        return processed_data

    def _create_streaming_excel(self, total_records, batch_size):
        """Create Excel file with streaming to handle massive datasets"""
        output = io.BytesIO()
        
        # Optimized for massive datasets
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'constant_memory': True,
            'strings_to_urls': False,
            'strings_to_numbers': False,
            'default_date_format': 'yyyy-mm-dd hh:mm:ss',
            'tmpdir': '/tmp',  # Use temp directory for large files
        })
        
        sheet = workbook.add_worksheet('Tasks')
        
        # Headers
        headers = [
            'Task ID', 'Task Name', 'Customer', 'Project', 'Stage', 
            'Created By', 'Created On', 'Assignees'
        ]
        
        # Write headers with formatting
        header_format = workbook.add_format({
            'bold': True, 
            'bg_color': '#D3D3D3',
            'border': 1
        })
        
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
        
        # Set column widths
        sheet.set_column(0, 0, 10)  # Task ID
        sheet.set_column(1, 1, 30)  # Task Name
        sheet.set_column(2, 2, 20)  # Customer
        sheet.set_column(3, 3, 25)  # Project
        sheet.set_column(4, 4, 15)  # Stage
        sheet.set_column(5, 5, 15)  # Created By
        sheet.set_column(6, 6, 20)  # Created On
        sheet.set_column(7, 7, 30)  # Assignees
        
        # Process in large chunks
        domain = []
        if self.max_records > 0:
            task_ids = self.env['project.task'].search(domain, limit=self.max_records)
        else:
            task_ids = self.env['project.task'].search(domain)
        
        total_tasks = len(task_ids)
        row = 1
        
        _logger.info(f"Starting streaming export of {total_tasks} tasks")
        
        for i in range(0, total_tasks, batch_size):
            batch_tasks = task_ids[i:i + batch_size]
            
            # Process batch
            batch_data = self._process_super_chunk(batch_tasks)
            
            # Write batch data
            for record in batch_data:
                sheet.write(row, 0, record['task_id'])
                sheet.write(row, 1, record['task_name'][:255])  # Limit length
                sheet.write(row, 2, record['customer'][:255])
                sheet.write(row, 3, record['project'][:255])
                sheet.write(row, 4, record['stage'][:255])
                sheet.write(row, 5, record['created_by'][:255])
                sheet.write(row, 6, record['created_on'])
                sheet.write(row, 7, record['assignees'][:255])
                row += 1
            
            # Update progress
            self.processed_records = min(i + batch_size, total_tasks)
            self.progress_percentage = (self.processed_records / total_tasks) * 100
            
            # Log progress
            _logger.info(f"Processed {self.processed_records}/{total_tasks} tasks ({self.progress_percentage:.1f}%)")
            
            # Force garbage collection
            gc.collect()
        
        workbook.close()
        output.seek(0)
        xlsx_data = output.read()
        output.close()
        
        return xlsx_data

    def start_massive_export(self):
        """Start the massive export process"""
        start_time = time.time()
        
        try:
            # Get total count
            total_count = self._get_task_count()
            self.total_records = total_count
            
            _logger.info(f"Starting massive export of {total_count} tasks")
            
            if total_count == 0:
                raise UserError(_("No tasks found to export."))
            
            # Warn for very large datasets
            if total_count > 200000:
                _logger.warning(f"Very large dataset detected: {total_count} records")
            
            # Update status
            self.status = 'processing'
            
            # Create Excel file with streaming
            xlsx_data = self._create_streaming_excel(total_count, self.batch_size)
            
            # Save file
            self.file_data = base64.b64encode(xlsx_data)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.file_name = f'massive_tasks_{self.processed_records}_{timestamp}.xlsx'
            
            # Update status
            self.status = 'completed'
            self.progress_percentage = 100.0
            
            elapsed_time = time.time() - start_time
            _logger.info(f"Massive export completed in {elapsed_time:.2f} seconds")
            
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/?model={self._name}&id={self.id}&field=file_data&filename={self.file_name}&download=true',
                'target': 'self',
            }
            
        except Exception as e:
            self.status = 'error'
            _logger.error(f"Massive export failed: {str(e)}")
            raise UserError(_("Export failed: %s") % str(e))

    def get_export_info(self):
        """Get export information"""
        total_tasks = self._get_task_count()
        estimated_time = total_tasks / 10000 * 60  # Rough estimate: 1 minute per 10K records
        file_size_mb = total_tasks * 0.001  # Rough estimate: 1KB per record
        
        return {
            'total_tasks': total_tasks,
            'estimated_time_minutes': estimated_time,
            'estimated_file_size_mb': file_size_mb,
            'recommended_batch_size': min(10000, max(1000, total_tasks // 20))
        }

    @api.model
    def create_export_job(self, batch_size=10000, max_records=0):
        """Create a new export job"""
        wizard = self.create({
            'batch_size': batch_size,
            'max_records': max_records
        })
        return wizard.start_massive_export()