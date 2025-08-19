from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import calendar


class OperationActivityWizard(models.TransientModel):
    _name = "operation.activity.wizard"
    _description = "Operation Activity Wiz"

    date_from = fields.Date(string="Date From", default=datetime.today().replace(day=1))
    date_to = fields.Date(
        string="Date To",
        default=datetime(datetime.today().year, datetime.today().month, 1)
        + relativedelta(months=1, days=-1),
        required="1",
    )
    team_ids = fields.Many2many("crm.team", string="Project Team")
    # employee_ids = fields.Many2many("hr.employee", string="Employee")
    status = fields.Selection(
        [
            ("new", "New"),
            ("inprogress", "In Progress"),
            ("done", "Done"),
            ("cancel", "Cancel"),
        ],
    )
    taken_days = fields.Float("Taken Day's Greater Than")
    operation_activity_ids = fields.Many2many(
        "activity.type.config", string="Operation Activity"
    )
            
    def fetch_data(self):

        view_id = self.env.ref(
            "scs_operation_report.operation_task_activity_tree_view"
        ).id
        domain = []

        if self.date_from:
            domain.append(("start_date", ">=", self.date_from))
        if self.date_to and self.status in ["done", "cancel"]:
            domain.append(("end_date", "<=", self.date_to))
        else:
            domain.append(("start_date", "<=", self.date_to))
        if self.team_ids:
            employee_ids = self.team_ids.team_members_ids.mapped('employee_ids').ids
            domain.append(("employee_id", "in", employee_ids))
        # if self.employee_ids:
            # domain.append(("employee_id", "in", self.employee_ids.ids))
        if self.status:
            domain.append(("status", "=", self.status))
        if self.taken_days:
            domain.append(("taken_days", ">=", self.taken_days))
        if self.operation_activity_ids:
            domain.append(
                ("operation_activity_id", "in", self.operation_activity_ids.ids)
            )

        res_ids = self.env["operation.task.activity"].search(domain)

        header = f"Operation Task Activity Report From {self.date_from or ''} To {self.date_to or ''}"
        return {
            "name": _(header),
            "type": "ir.actions.act_window",
            "view_mode": "tree,pivot",
            "res_model": "operation.task.activity",
            "view_id": view_id,
            "views": [(view_id, "tree"), [False, "pivot"]],
            "domain": [("id", "in", res_ids.ids)],
            "target": "main",
            "context": {"create": False},
        }

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_from > rec.date_to:
                raise UserError(_("End Date Must be Greater then Start Date"))
