from odoo import models, fields, api, _
from odoo.exceptions import UserError
import io
import xlsxwriter
import base64
import logging
import time
from datetime import datetime

_logger = logging.getLogger(__name__)


class ProjectTaskExportWizard(models.TransientModel):
    _name = 'project.task.export.wizard'
    _description = 'Wizard to Export Project Tasks in XLSX'

    file_data = fields.Binary('File')
    file_name = fields.Char('Filename', default='project_tasks.xlsx')
    export_type = fields.Selection([
        ('basic', 'Basic Export (Fast)'),
        ('full', 'Full Export (Slow)'),
        ('stream', 'Stream Export (Memory Efficient)')
    ], default='basic', required=True)
    max_records = fields.Integer('Max Records', default=5000,
                                help="Maximum number of records to export (0 = all records, max recommended: 5,000)")
    
    # Status fields
    export_status = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('error', 'Error')
    ], default='draft')
    progress = fields.Float('Progress %', default=0.0)
    error_message = fields.Text('Error Message')

    def _safe_extract_name(self, field_value):
        """Safely extract name from Many2one field"""
        if not field_value:
            return ''
        if isinstance(field_value, (list, tuple)) and len(field_value) >= 2:
            return str(field_value[1])
        elif hasattr(field_value, 'name'):
            return field_value.name
        else:
            return str(field_value)

    def _get_task_data_batch(self, task_ids, batch_size=500):
        """Get task data in batches to avoid memory issues"""
        all_data = []
        total_batches = (len(task_ids) + batch_size - 1) // batch_size
        
        for i in range(0, len(task_ids), batch_size):
            batch_tasks = task_ids[i:i + batch_size]
            batch_data = self._process_task_batch(batch_tasks)
            all_data.extend(batch_data)
            
            # Update progress
            progress = ((i // batch_size) + 1) / total_batches * 80  # 80% for data processing
            self.progress = progress
            
            # Commit every batch to avoid long transactions
            self.env.cr.commit()
            
            _logger.info(f"Processed batch {(i // batch_size) + 1}/{total_batches} - {len(batch_data)} records")
        
        return all_data

    def _process_task_batch(self, task_ids):
        """Process a batch of tasks with optimized field reading"""
        if self.export_type == 'basic':
            return self._process_basic_batch(task_ids)
        elif self.export_type == 'full':
            return self._process_full_batch(task_ids)
        else:
            return self._process_stream_batch(task_ids)

    def _process_basic_batch(self, task_ids):
        """Process batch with basic fields only - fastest method"""
        fields_to_read = [
            'name', 'partner_id', 'project_id', 'stage_id', 
            'create_uid', 'create_date', 'user_ids'
        ]
        
        # Use search_read for better performance
        domain = [('id', 'in', task_ids.ids)]
        tasks_data = self.env['project.task'].search_read(domain, fields_to_read)
        
        processed_data = []
        for task_data in tasks_data:
            # Get assignees efficiently
            assignees = ''
            if task_data.get('user_ids'):
                try:
                    user_ids = task_data['user_ids']
                    if user_ids:
                        users = self.env['res.users'].browse(user_ids)
                        assignees = ', '.join(users.mapped('name'))
                except Exception as e:
                    _logger.warning(f"Error getting assignees for task {task_data.get('id')}: {e}")
            
            processed_data.append({
                'task_name': task_data.get('name', ''),
                'customer': self._safe_extract_name(task_data.get('partner_id')),
                'project': self._safe_extract_name(task_data.get('project_id')),
                'stage': self._safe_extract_name(task_data.get('stage_id')),
                'created_by': self._safe_extract_name(task_data.get('create_uid')),
                'created_on': str(task_data.get('create_date', '')),
                'assignees': assignees
            })
        
        return processed_data

    def _process_full_batch(self, task_ids):
        """Process batch with full field data"""
        fields_to_read = [
            'name', 'partner_id', 'sale_order_id', 'project_id', 
            'stage_id', 'create_uid', 'create_date', 'booking_type',
            'tag_ids', 'user_ids'
        ]
        
        domain = [('id', 'in', task_ids.ids)]
        tasks_data = self.env['project.task'].search_read(domain, fields_to_read)
        
        processed_data = []
        for task_data in tasks_data:
            # Get related data efficiently
            tags = ''
            assignees = ''
            
            try:
                # Tags
                if task_data.get('tag_ids'):
                    tag_records = self.env['project.tags'].browse(task_data['tag_ids'])
                    tags = ', '.join(tag_records.mapped('name'))
                
                # Assignees
                if task_data.get('user_ids'):
                    user_records = self.env['res.users'].browse(task_data['user_ids'])
                    assignees = ', '.join(user_records.mapped('name'))
                
            except Exception as e:
                _logger.warning(f"Error getting related data for task {task_data.get('id')}: {e}")
            
            processed_data.append({
                'task_name': task_data.get('name', ''),
                'customer': self._safe_extract_name(task_data.get('partner_id')),
                'sale_order': self._safe_extract_name(task_data.get('sale_order_id')),
                'project': self._safe_extract_name(task_data.get('project_id')),
                'stage': self._safe_extract_name(task_data.get('stage_id')),
                'created_by': self._safe_extract_name(task_data.get('create_uid')),
                'created_on': str(task_data.get('create_date', '')),
                'booking_type': task_data.get('booking_type', ''),
                'tags': tags,
                'assignees': assignees
            })
        
        return processed_data

    def _process_stream_batch(self, task_ids):
        """Process batch with streaming approach - most memory efficient"""
        return self._process_basic_batch(task_ids)  # Use basic for streaming

    def _create_excel_file_optimized(self, data, export_type='basic'):
        """Create Excel file with memory optimization"""
        output = io.BytesIO()
        
        # Optimize workbook settings for large files
        workbook_options = {
            'constant_memory': True,
            'strings_to_urls': False,
            'strings_to_numbers': False,
            'default_date_format': 'yyyy-mm-dd hh:mm:ss',
        }
        
        # Add use_zip64 only if supported (newer versions)
        try:
            workbook_options['use_zip64'] = True
        except:
            pass
        
        workbook = xlsxwriter.Workbook(output, workbook_options)
        sheet = workbook.add_worksheet('Tasks')
        
        # Try to set optimization if available (newer versions)
        try:
            sheet.set_optimization()
        except AttributeError:
            # Method not available in older versions, continue without it
            _logger.info("set_optimization() not available in this XlsxWriter version")
        
        # Define headers based on export type
        if export_type == 'basic' or export_type == 'stream':
            headers = [
                'Task Name', 'Customer', 'Project', 'Stage',
                'Created By', 'Created On', 'Assignees'
            ]
            data_keys = [
                'task_name', 'customer', 'project', 'stage',
                'created_by', 'created_on', 'assignees'
            ]
        else:
            headers = [
                'Task Name', 'Customer', 'Sales Order', 'Project', 'Stage',
                'Tags', 'Created By', 'Created On', 'Assignees', 'Booking Type'
            ]
            data_keys = [
                'task_name', 'customer', 'sale_order', 'project', 'stage',
                'tags', 'created_by', 'created_on', 'assignees', 'booking_type'
            ]
        
        # Write headers
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3'})
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
        
        # Write data in chunks to avoid memory issues
        chunk_size = 1000
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            
            for row_idx, row_data in enumerate(chunk, i + 1):
                for col_idx, key in enumerate(data_keys):
                    value = row_data.get(key, '')
                    
                    # Truncate very long strings
                    if isinstance(value, str) and len(value) > 1000:
                        value = value[:1000] + '...'
                    
                    sheet.write(row_idx, col_idx, value)
            
            # Update progress
            progress = 80 + (i / len(data)) * 20  # 20% for file creation
            self.progress = progress
            
            if i % 5000 == 0:  # Commit every 5000 rows
                self.env.cr.commit()
        
        # Auto-adjust columns (but limit width)
        for col_idx in range(len(headers)):
            sheet.set_column(col_idx, col_idx, min(30, max(10, len(headers[col_idx]) + 2)))
        
        workbook.close()
        xlsx_data = output.getvalue()
        output.close()
        
        if not xlsx_data:
            raise UserError(_("Generated XLSX file is empty. Please check data and try again."))
        
        return xlsx_data

    def export_project_tasks_xlsx(self):
        """Main export method with timeout prevention"""
        self.ensure_one()
        start_time = time.time()
        
        try:
            self.write({
                'export_status': 'running',
                'progress': 0.0,
                'error_message': False
            })
            self.env.cr.commit()
            
            # Get task count first
            domain = []
            total_count = self.env['project.task'].search_count(domain)
            
            # Determine actual limit
            if self.max_records > 0:
                actual_limit = min(self.max_records, total_count)
            else:
                actual_limit = total_count
            
            # Safety check for very large datasets
            if actual_limit > 10000:
                raise UserError(_(
                    "Dataset too large (%d records). Please set maximum records to 10,000 or less. "
                    "For larger exports, consider using filtered views or contact your administrator."
                ) % actual_limit)
            
            _logger.info(f"Starting export of {actual_limit} tasks (total: {total_count}) with {self.export_type} mode")
            
            # Get task IDs
            task_ids = self.env['project.task'].search(domain, limit=actual_limit, order='id')
            
            if not task_ids:
                raise UserError(_("No tasks found to export."))
            
            # Process data in batches
            batch_size = 500 if self.export_type == 'basic' else 200
            processed_data = self._get_task_data_batch(task_ids, batch_size)
            
            # Create Excel file
            self.progress = 80.0
            self.env.cr.commit()
            
            xlsx_data = self._create_excel_file_optimized(processed_data, self.export_type)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f'project_tasks_{self.export_type}_{len(processed_data)}_{timestamp}.xlsx'
            
            # Save file data
            self.write({
                'file_data': base64.b64encode(xlsx_data),
                'file_name': file_name,
                'export_status': 'done',
                'progress': 100.0
            })
            
            elapsed_time = time.time() - start_time
            _logger.info(f"Export completed successfully in {elapsed_time:.2f} seconds - {len(processed_data)} records")
            
            # Return download action
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content?model=project.task.export.wizard&id={self.id}&field=file_data&filename_field=file_name&download=true',
                'target': 'self',
            }
            
        except Exception as e:
            _logger.error("Export failed: %s", str(e), exc_info=True)
            self.write({
                'export_status': 'error',
                'error_message': str(e),
                'progress': 0.0
            })
            raise UserError(_("Export failed: %s") % str(e))

    @api.model
    def get_export_stats(self):
        """Get export statistics for UI"""
        task_count = self.env['project.task'].search_count([])
        return {
            'total_tasks': task_count,
            'recommended_mode': 'stream' if task_count > 2000 else 'basic' if task_count > 1000 else 'full',
            'max_safe_records': 10000
        }

    def action_reset_export(self):
        """Reset export status for retry"""
        self.write({
            'export_status': 'draft',
            'progress': 0.0,
            'error_message': False,
            'file_data': False,
            'file_name': 'project_tasks.xlsx'
        })
        return {'type': 'ir.actions.act_window_close'}