import csv
import base64
import io
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

_logger = logging.getLogger(__name__)

class ProjectTaskImportWizard(models.TransientModel):
    _name = 'project.task.import.wizard'
    _description = 'Import Project Tasks from CSV'

    csv_file = fields.Binary(string="Upload CSV", required=True)
    file_name = fields.Char(string="File Name")

    failed_csv_file = fields.Binary(string="Failed Records CSV", readonly=True)
    failed_file_name = fields.Char(string="Failed File Name")

    def parse_date(self, date_str):
        """Try parsing date in different formats."""
        for fmt in ("%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    def action_upload_tasks(self):
        _logger.info("📥 Starting task import from CSV")

        if not self.csv_file:
            raise UserError("Please upload a CSV file.")

        file_content = base64.b64decode(self.csv_file).decode("utf-8")
        csv_data = list(csv.reader(io.StringIO(file_content)))

        if not csv_data:
            raise UserError("CSV file is empty!")

        header = csv_data[0]
        data_rows = csv_data[1:]
        failed_records = []
        task_count = 0
        upd_task_count = 0

        for row in data_rows:
            if len(row) < 8:
                _logger.warning("Row skipped: insufficient data: %s", row)
                failed_records.append(row + ["Insufficient data"])
                continue

            title, project_name, sales_order_ref, schedule_date_str, project_teams, tags, stage, assignee = [x.strip() for x in row[:8]]

            errors = []
            if not title:
                errors.append("Title missing")
            if not project_name:
                errors.append("Project missing")
            if not stage:
                errors.append("Stage missing")
            if not assignee:
                errors.append("Assignee missing")

            schedule_date = self.parse_date(schedule_date_str) if schedule_date_str else False
            if schedule_date_str and not schedule_date:
                errors.append("Invalid date format")

            if errors:
                _logger.warning("Row has validation errors: %s", errors)
                failed_records.append(row + [", ".join(errors)])
                continue

            project = self.env['project.project'].search([('name', '=', project_name)], limit=1)
            if not project:
                _logger.warning("Project not found: %s", project_name)
                failed_records.append(row + ["Project not found"])
                continue

            sale_order = sale_line = False
            if sales_order_ref:
                sale_order = self.env['sale.order'].search([('name', '=', sales_order_ref)], limit=1)
                if sale_order:
                    sale_line = self.env['sale.order.line'].search([('order_id', '=', sale_order.id)], limit=1)

            partner_id = sale_order.partner_id.id if sale_order else False
            project_team_ids = self.env['crm.team'].search([('name', 'in', project_teams.split(','))]).ids if project_teams else []
            tag_ids = self.env['project.tags'].search([('name', 'in', tags.split(','))]).ids if tags else []
            stage_id = self.env['project.task.type'].search([('name', '=', stage)], limit=1)

            if not stage_id:
                _logger.warning("Stage not found: %s", stage)
                failed_records.append(row + ["Stage not found"])
                continue

            assignees = self.env['res.users'].search([('name', 'ilike', assignee)])
            if not assignees:
                _logger.warning("Assignee not found: %s", assignee)
                failed_records.append(row + ["Assignee not found"])
                continue

            existing_task = self.env['project.task'].search([
                ('sale_order_id', '=', sale_order.id),
                ('project_id', '=', project.id)
            ], limit=1) if sale_order else False

            task_vals = {
                'name': title,
                'project_id': project.id,
                'sale_order_id': sale_order.id if sale_order else False,
                'sale_line_id': sale_line.id if sale_line else False,
                'partner_id': partner_id,
                'schedule_date': schedule_date,
                'project_team_ids': [(6, 0, project_team_ids)],
                'user_ids': [(6, 0, assignees.ids)],
                'tag_ids': [(6, 0, tag_ids)],
                'stage_id': stage_id.id,
            }

            if existing_task:
                existing_task.write(task_vals)
                _logger.info("✅ Task updated: %s", existing_task.name)
                upd_task_count += 1
            else:
                self.env['project.task'].create(task_vals)
                _logger.info("✅ Task created: %s", title)
                task_count += 1

        if failed_records:
            failed_csv_output = io.StringIO()
            csv_writer = csv.writer(failed_csv_output)
            csv_writer.writerow(header + ["Error Message"])
            csv_writer.writerows(failed_records)
            self.failed_csv_file = base64.b64encode(failed_csv_output.getvalue().encode('utf-8'))
            self.failed_file_name = "failed_records.csv"
            _logger.warning("⚠️ %d records failed during import.", len(failed_records))

        _logger.info("🎉 Task import finished. Created: %d, Updated: %d", task_count, upd_task_count)

        return {
            'effect': {
                'fadeout': 'slow',
                'message': f'{task_count} tasks have been created and {upd_task_count} tasks updated successfully.',
                'type': 'rainbow_man',
            },
            'type': 'ir.actions.act_window_close',
        }

    # def action_upload_tasks(self):
    #     print("\n\n\nAction Upload Tasks Called")
    #     """Read CSV file and create tasks. Save failed records in a new CSV."""
    #     if not self.csv_file:
    #         raise UserError("Please upload a CSV file.")

    #     file_content = base64.b64decode(self.csv_file).decode("utf-8")
    #     csv_data = list(csv.reader(io.StringIO(file_content)))

    #     if not csv_data:
    #         raise UserError("CSV file is empty!")

    #     header = csv_data[0]
    #     data_rows = csv_data[1:]
    #     failed_records = []
    #     task_count = 0
    #     upd_task_count = 0

    #     for row in data_rows:
    #         if len(row) < 8:
    #             print("\n\n\nRow is less than 8",row)
    #             failed_records.append(row + ["Insufficient data"])
    #             continue

    #         title, project_name, sales_order_ref, schedule_date_str, project_teams, tags, stage, assignee = row[:8]

    #         schedule_date = self.parse_date(schedule_date_str)
    #         if not schedule_date:
    #             print("\n\n\nInvalid date format for row:", row)
    #             failed_records.append(row + ["Invalid date format"])
    #             continue

    #         project = self.env['project.project'].search([('name', '=', project_name)], limit=1)
    #         print("\n\n\nProject:",project)
    #         if not project:
    #             print("\n\n\nProject not found for row:", row)
    #             failed_records.append(row + ["Project not found"])
    #             continue

    #         sale_order = self.env['sale.order'].search([('name', '=', sales_order_ref)], limit=1)
    #         sale_line = self.env['sale.order.line'].search([('order_id', '=', sale_order.id)], limit=1)

    #         partner_id = sale_order.partner_id.id if sale_order else False
    #         project_team_ids = [team.id for team in self.env['crm.team'].search([('name', 'in', project_teams.split(','))])]
    #         tag_ids = [tag.id for tag in self.env['project.tags'].search([('name', 'in', tags.split(','))])]
    #         stage_id = self.env['project.task.type'].search([('name', '=', stage)], limit=1)

    #         if not stage_id:
    #             print("\n\n\nStage not found for row:", row)
    #             failed_records.append(row + ["Stage not found"])
    #             continue

    #         assign_ids = self.env['res.users'].search([('name', '=', assignee)])
    #         if not assign_ids:
    #             print("\n\n\nAssignee not found for row:", row)
    #             failed_records.append(row + ["Assignee not found"])
    #             continue

    #         existing_task = self.env['project.task'].search([('sale_order_id', '=', sale_order.id), ('project_id', '=', project.id)], limit=1)

    #         if existing_task:
    #             existing_task.write({
    #                 'project_id': project.id,
    #                 'sale_order_id': sale_order.id,
    #                 'sale_line_id': sale_line.id,
    #                 'partner_id': partner_id,
    #                 'schedule_date': schedule_date,
    #                 'project_team_ids': [(6, 0, project_team_ids)],
    #                 'user_ids': [(6, 0, assign_ids.ids)],
    #                 'tag_ids': [(6, 0, tag_ids)],
    #                 'stage_id': stage_id.id,
    #             })
    #             print("\n\n\nexisting_task existing_task",existing_task)
    #             upd_task_count += 1
    #         else:
    #             self.env['project.task'].create({
    #                 'name': title,
    #                 'project_id': project.id,
    #                 'sale_order_id': sale_order.id,
    #                 'sale_line_id': sale_line.id,
    #                 'partner_id': partner_id,
    #                 'schedule_date': schedule_date,
    #                 'project_team_ids': [(6, 0, project_team_ids)],
    #                 'user_ids': [(6, 0, assign_ids.ids)],
    #                 'tag_ids': [(6, 0, tag_ids)],
    #                 'stage_id': stage_id.id,
    #             })
    #             task_count += 1

    #     # Handle failed records
    #     if failed_records:
    #         failed_csv_output = io.StringIO()
    #         csv_writer = csv.writer(failed_csv_output)
    #         csv_writer.writerow(header + ["Error Message"])
    #         csv_writer.writerows(failed_records)
    #         self.failed_csv_file = base64.b64encode(failed_csv_output.getvalue().encode('utf-8'))
    #         self.failed_file_name = "failed_records.csv"

    #     return {
    #         'effect': {
    #             'fadeout': 'slow',
    #             'message': f'{task_count} tasks have been created successfully and {upd_task_count} tasks updated successfully',
    #             'type': 'rainbow_man',
    #         },
    #         'type': 'ir.actions.act_window_close',
    #     }



# import csv
# import base64
# import io
# from odoo import models, fields, api
# from odoo.exceptions import UserError
# from datetime import datetime


# class ProjectTaskImportWizard(models.TransientModel):
#     _name = 'project.task.import.wizard'
#     _description = 'Import Project Tasks from CSV'

#     csv_file = fields.Binary(string="Upload CSV", required=True)
#     file_name = fields.Char(string="File Name")

#     failed_csv_file = fields.Binary(string="Failed Records CSV", readonly=True)
#     failed_file_name = fields.Char(string="Failed File Name")

#     def parse_date(self, date_str):
#         """Try parsing date in different formats."""
#         for fmt in ("%m/%d/%Y", "%d/%m/%Y"):
#             try:
#                 return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
#             except ValueError:
#                 continue
#         return None

#     def action_upload_tasks(self):
#         """Read CSV file and create tasks with project teams and sales order item."""
#         if not self.csv_file:
#             raise UserError("Please upload a CSV file.")

#         file_content = base64.b64decode(self.csv_file).decode("utf-8")
#         csv_data = list(csv.reader(file_content.splitlines()))

#         if not csv_data:
#             raise UserError("CSV file is empty!")

#         header = csv_data[0]
#         data_rows = csv_data[1:]

#         task_count = 0

#         for row in data_rows:
#             if len(row) < 8:
#                 continue

#             title, project_name, sales_order_ref, schedule_date_str, project_teams, tags, stage, assignee = row[:8]

#             schedule_date = self.parse_date(schedule_date_str)
#             if not schedule_date:
#                 failed_records.append(row + ["Invalid date format"])
#                 continue
            
#             project = self.env['project.project'].search([('name', '=', project_name)], limit=1)

#             sale_order = self.env['sale.order'].search([('name', '=', sales_order_ref)], limit=1)
#             sale_line = self.env['sale.order.line'].search([('order_id', '=', sale_order.id)], limit=1)
            
#             partner_id = sale_order.partner_id.id if sale_order else False
            
#             project_team_ids = []
#             team_names = [name.strip() for name in project_teams.split(',')]
            
#             tag_names = [t.strip() for t in tags.split(',')]
#             tag_ids = self.env['project.tags'].search([('name', 'in', tag_names)]).ids
            
#             stage_id = self.env['project.task.type'].search([('name', '=', stage)], limit=1)
#             if not stage_id:
#                 failed_records.append(row + ["Stage not found"])
#                 continue

#             # Ensure assignee exists
#             assign_ids = self.env['res.users'].search([('name', '=', assignee)])

#             print("\n\n\nAssign IDs:", assign_ids)

#             existing_task = self.env['project.task'].search([
#                 ('name', '=', title),
#             ], limit=1)
#             print("\n\n\nExistingggggggggg",existing_task,title)

#             if existing_task:
#                 if assign_ids:
#                     existing_task.write({
#                         'sale_order_id': sale_order.id,
#                         'user_ids': [(6, 0, assign_ids.ids)],
#                     })
#                     print("\n\n\nUpdated Task:", existing_task)
#                 else:
#                     print("\n\n\nAssignee not found:", assignee)
#             else:
#                 self.env['project.task'].create({
#                     'name': title,
#                     'project_id': project.id,
#                     'sale_order_id': sale_order.id,
#                     'sale_line_id': sale_line.id,
#                     'partner_id': sale_line.order_id.partner_id.id,
#                     'schedule_date': schedule_date,
#                     'project_team_ids': [(6, 0, project_team_ids)],
#                     'user_ids': [(6, 0, assign_ids.ids)],
#                     'tag_ids': [(6, 0, tag_ids)],
#                     'stage_id': stage_id.id,
#                 })
#                 self._cr.commit()
#                 task_count += 1

#         return {
#             'effect': {
#                 'fadeout': 'slow',
#                 'message': f'{task_count} tasks have been created successfully!',
#                 'type': 'rainbow_man',
#             },
#             'type': 'ir.actions.act_window_close',
#         }