import base64
import csv
from io import StringIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class UpdateAssigneeWizard(models.TransientModel):
    _name = 'update.assignee.wizard'
    _description = 'Update Assignee Wizard'

    booking_files = fields.Binary("Upload CSV File", required=True, attachment=False)
    filename = fields.Char('Filename')
    assignee_ids = fields.Many2many('res.users', string='Assignees', required=True)
    stage_ids = fields.Many2many('project.task.type', string='Stages', required=True)
    project_team_ids = fields.Many2many('crm.team', string='Project Teams')  # Many2many as per your model

    def action_apply(self):
        if not self.booking_files:
            raise UserError(_("Please upload a CSV file containing a 'Booking' column."))

        try:
            decoded_file = base64.b64decode(self.booking_files).decode('utf-8')
            csv_reader = csv.DictReader(StringIO(decoded_file), delimiter=',')
        except Exception as e:
            raise UserError(_("Invalid file format. Error: %s") % str(e))

        booking_values = []
        for row in csv_reader:
            booking = row.get('Booking')
            if booking:
                booking_values.append(booking.strip())

        if not booking_values:
            raise UserError(_("No valid 'Booking' values found in the file."))

        domain = [
            ('sale_order_id', 'in', booking_values),
            ('stage_id', 'in', self.stage_ids.ids),
        ]
        matched_tasks = self.env['project.task'].search(domain)

        if not matched_tasks:
            raise UserError(_("No matching tasks found for the given Bookings and Stages."))

        for task in matched_tasks:
            for team in self.project_team_ids:
                if team not in task.project_team_ids:
                    task.project_team_ids = [(4, team.id)]
            for user in self.assignee_ids:
                if user not in task.user_ids:
                    task.user_ids = [(4, user.id)]

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success"),
                'message': _("%d task(s) updated successfully." % len(matched_tasks)),
                'type': 'success',
                'sticky': False,
            }
        }


# import base64
# import csv
# from io import StringIO

# from odoo import models, fields, api, _
# from odoo.exceptions import UserError


# class UpdateAssigneeWizard(models.TransientModel):
#     _name = 'update.assignee.wizard'
#     _description = 'Update Assignee Wizard'

#     booking_files = fields.Binary("Upload CSV File", required=True, attachment=False)
#     # booking_files = fields.Binary('Booking File (.csv)', required=True)
#     filename = fields.Char('Filename')  # Optional, helps identify uploaded file
#     assignee_ids = fields.Many2many('res.users', string='Assignees', required=True)
#     stage_ids = fields.Many2many('project.task.type', string='Stages', required=True)
#     project_team_ids = fields.Many2many('crm.team', string='Project Team', required=True)

#     def action_apply(self):
#         # Check if file is provided
#         print("\n\n\nBooking Files:", self.booking_files)
#         if not self.booking_files:
#             raise UserError(_("Please upload a CSV file containing 'Booking' values."))
        
#         # Decode base64 file and prepare CSV reader
#         try:
#             print("\n\n\nDecoding booking files...")
#             # decoded_file = base64.b64decode(self.booking_files)
#             # file_content = decoded_file.decode('utf-8')
#             # csv_reader = csv.DictReader(StringIO(file_content))
#             decoded_file = base64.b64decode(self.booking_files).decode('utf-8')
#             csv_reader = csv.DictReader(StringIO(decoded_file), delimiter=',')
#         except Exception as e:
#             raise UserError(_("Invalid file format. Please upload a valid CSV file.\nError: %s" % str(e)))

#         # Collect all booking values
#         booking_values = []
#         for row in csv_reader:
#             booking = row.get('Booking')
#             if booking:
#                 booking_values.append(booking.strip())

#         if not booking_values:
#             raise UserError(_("No 'Booking' values found in the file. Ensure the column name is exactly 'Booking'."))

#         # Search for matching project tasks
#         domain = [
#             ('sale_order_id', 'in', booking_values),
#             ('stage_id', 'in', self.stage_ids.ids),
#         ]
#         matched_tasks = self.env['project.task'].search(domain)

#         if not matched_tasks:
#             raise UserError(_("No matching tasks found for the given Bookings and Stages."))

#         # Apply updates
#         for task in matched_tasks:
#             if self.project_team_ids:
#                 task.project_team_ids = self.project_team_ids[0].id  # Only one team can be assigned (Many2one)
#             task.user_ids = [(6, 0, self.assignee_ids.ids)]  # Replace all assignees

#         # Success notification
#         return {
#             'type': 'ir.actions.client',
#             'tag': 'display_notification',
#             'params': {
#                 'title': _("Success"),
#                 'message': _("%d task(s) updated successfully." % len(matched_tasks)),
#                 'type': 'success',
#                 'sticky': False,
#             }
#         }
