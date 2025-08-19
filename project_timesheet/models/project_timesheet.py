# See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    def _set_default(self):
        type_id = self.env["timesheet.type"].search(
            [("is_default", "=", True)], limit=1
        )
        return type_id and type_id.id or False

    timesheet_type = fields.Many2one(
        "timesheet.type", string="Type", default=_set_default
    )

    ticket_no = fields.Char(string="Ticket No")

    @api.model
    def create(self, vals):
        dict_to_pass = {}
        if vals.get("project_id"):
            dict_to_pass = {"call_from_project": True}
        if self._context.get("from_event", False):
            dict_to_pass.update({"from_event": True})
        return super(AccountAnalyticLine, self.with_context(dict_to_pass)).create(vals)

    def write(self, vals):
        """
        This method will allow user to edit timesheet line of
        meeting attendees once task of meeting type
        is created.
        """
        dict_to_pass = {}
        for rec in self:
            task_id = rec.sudo().task_id
            if task_id.project_id:
                dict_to_pass = {"call_from_project": True}
            if (
                task_id
                and task_id.task_type == "meeting"
                and task_id.reviewer_id.id == self._uid
            ):
                return (
                    super(AccountAnalyticLine, rec.sudo())
                    .with_context({"from_event": True})
                    .write(vals)
                )
            if self._context.get("from_event", False):
                dict_to_pass.update({"from_event": True})
        return super(AccountAnalyticLine, self.with_context(dict_to_pass)).write(vals)


    @api.onchange("project_id")
    def _onchange_project_id(self):
        """
        Add Project in the Timesheet to be selected and it
        will set the analytic account related to the project
        ----------------------------------------------------
        @param self : object pointer
        """
        super(AccountAnalyticLine, self)._onchange_project_id()
        for ts in self:
            project_id = ts.project_id
            ts.account_id = project_id and project_id.analytic_account_id.id or False

    @api.constrains("date", "unit_amount")
    def _check_work_summary(self):
        context = self._context
        context = self._context
        if context.get("call_from_project", False):
            user = self.env.user
            cr = self.env.cr
            if self.user_id:
                ana_ts_lines = self.search(
                    [("user_id", "=", self.user_id.id), ("date", "=", self.date)]
                )
                unit_amt = sum([ana_ts.unit_amount for ana_ts in ana_ts_lines])
                date_check = self.date.strftime("%d-%m-%Y")
                if unit_amt > 24:
                    raise ValidationError(
                        _("In a single day you can fill 24 hours of timesheet '%s'")
                        % self.user_id.name.title()
                        + " "
                        + "and"
                        " for date '%s'" % date_check
                    )
            hr_manger = self.user_has_groups("hr.group_hr_manager")
            if self.date:
                if not hr_manger:
                    cr.execute(
                        """select id from hr_timesheet_sheet where \
                             user_id = %s and \
                             date_start <= %s and date_end >= %s """
                        """and state != 'draft'
                             """,
                        (self.user_id.id, self.date, self.date),
                    )
                    timesheet_rec = cr.fetchall()
                    if timesheet_rec:
                        raise ValidationError(
                            _("You can add work summary only in open timesheet!")
                        )
                if not hr_manger:
                    diff_days = user.company_id.timesheet_allow_hrs
                    curr_date = datetime.now().date()
                    last_day_temp = curr_date - relativedelta(days=diff_days)
                    for work in self:
                        if work.date.isoweekday() != diff_days:
                            if work.date <= last_day_temp:
                                raise ValidationError(
                                    _(
                                        "You can not add a work summary after "
                                        + str(diff_days)
                                        + " days"
                                    )
                                )

                            if work.date > datetime.today().date():
                                raise ValidationError(
                                    _("You cannot add work Summary for future date. ")
                                )
                        if work.date > curr_date:
                            raise ValidationError(
                                _("You can not add Timesheet entry in advance!")
                            )


class ResCompany(models.Model):
    _inherit = "res.company"

    timesheet_allow_hrs = fields.Integer(
        "Timesheet allow Days",
        help=""" This field is used to \
                                         restrict user from making entry in \
                                         timesheet before the days \
                                          specified.
                                         """,
        default=1,
    )
