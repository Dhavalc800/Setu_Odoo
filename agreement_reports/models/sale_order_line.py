from odoo import api, models, fields, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_refund = fields.Boolean("Is Refund")
    amount_received = fields.Monetary("Amount received")

    # def _timesheet_create_project_prepare_values(self):
    #     res = super()._timesheet_create_project_prepare_values()
    #     res.update({'active': False})
    #     return res

    def _timesheet_create_task_prepare_values(self, project):
        # project.active = False
        res = super()._timesheet_create_task_prepare_values(project)
        res.update({'active': False})
        return res

    def write(self, vals):
        res = super().write(vals)
        if 'is_refund' in vals:
            agreement = self.order_id.agreement_id
            if agreement and agreement.line_ids:
                agreement_line = agreement.line_ids.filtered(lambda line: line.product_id == self.product_id)
                if agreement_line:
                    agreement_line.is_refund = vals['is_refund']
        return res

    # @api.model
    # def fields_get(self, allfields=None, attributes=None):
    #     res = super().fields_get()
    #     if self.env.user.has_group(
    #         "account.group_account_user"
    #     ) or self.env.user.has_group("account.group_account_manager"):
    #         res["amount_received"]["readonly"] = False
    #     else:
    #         res["amount_received"]["readonly"] = True
    #     return res
