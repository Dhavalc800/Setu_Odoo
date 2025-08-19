# See LICENSE file for full copyright and licensing details.

from odoo import models, api
from odoo.exceptions import Warning


class ApproveTimesheetActivity(models.TransientModel):
    _name = 'approve.timesheet.activity'
    _description = 'Approve TimeSheet Activity'

    @api.multi
    def approve_timesheet(self):
        """
        A method to approve multiple timesheet by the Project Manager
        from wizard.
        -------------------------------------------------------
        """
        cr = self.env.cr
        user = self.env.user
        context = self.env.context
        if context.get('active_ids', False):
            analytic_rec = self.env['account.analytic.line'].\
                search([('state', '=', 'confirm'),
                        ('id', 'in', context[
                            'active_ids'])
                        ])
            for line in analytic_rec:
                if not user.id == 1:
                    if line.user_id.id == user.id:
                        raise Warning("You cannot approve your own Timesheet !")
                    if not line.project_id.user_id.id == user.id and not \
                    line.project_id.project_leader_id.id == user.id:
                        raise Warning("Only Project Manager/Leader can approve \
                                 the timesheet line!")
                cr.execute(
                    "update account_analytic_line set state='done' where \
                    id = %s", (line.id,))
