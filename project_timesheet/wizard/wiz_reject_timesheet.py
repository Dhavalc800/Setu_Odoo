# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError


class WizRejectTimesheet(models.TransientModel):

    _name = 'wiz.reject.ts'

    reject_reason = fields.Text('Reject Reason')

    @api.multi
    def reject(self):
        """
        This method will update the reason to reject the timesheet which
        is given in this wizard(popup).
        -------------------------------------------------------------
        @param self : object pointer
        @return True
        """
        for wiz in self:
            # Fetch the Active Model and Active ID
            # for the Timesheet which is to be rejected
            act_id = self._context.get('active_id')
            act_mdl = self._context.get('active_model')
            sheet_obj = self.env[act_mdl]
            ts_sheet = sheet_obj.browse(act_id)
            if act_mdl == 'account.analytic.line':
                sheet = ts_sheet.sheet_id
            elif act_mdl == 'hr_timesheet_sheet.sheet':
                sheet = ts_sheet
            elif act_mdl == 'hr.employee':
                sheet_id = self._context.get('sheet_id')
                sheet = self.env['hr_timesheet_sheet.sheet'].browse(sheet_id)
            usr_obj = self.env['res.users']
            usr = usr_obj.browse(self._uid)
            curr_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            # Update the timesheet rejection reason with
            # the timestamp and reason
            comments = '\n' + 'Rejection Date : ' + curr_date + '\n' + \
                'Rejected By : ' + usr.name
            if act_mdl == 'hr.analytic.timesheet':
                comments += '\n' + 'Project : ' + ts_sheet.project_id.name + \
                    "\n" + 'task: ' + ts_sheet.task_id.name
            if wiz.reject_reason:
                comments += '\n' + 'Reason: ' + wiz.reject_reason or ' ' + \
                    '\n' + '-' * 150 + '\n'
            sheet = sheet.sudo()
            if sheet.comments:
                comments += sheet.comments
            sheet.sudo().write({'state': 'draft'})
            for ts in sheet.timesheet_ids:
                if ts.state != 'done':
                    ts.write({'state': 'reject'})
            sheet.sudo().write({'state': 'reject',
                                'reject': True,
                                'comments': comments})

        return True
