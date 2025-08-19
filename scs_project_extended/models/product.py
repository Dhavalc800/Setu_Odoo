# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models, Command
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    dependent_project_ids = fields.Many2many(
        "project.project",
        "project_product_dependent_rel",
        "product_id",
        "project_id",
        string="Dependent Project",
    )

    @api.constrains("project_id", "dependent_project_ids")
    def _check_dependence(self):
        self._check_recursion_dependent_task()

    def _check_recursion_dependent_task(self):
        for rec in self:
            if (
                rec.dependent_project_ids
                and rec.project_id
                and rec.project_id.id in rec.dependent_project_ids.ids
            ):
                raise ValidationError(
                    _(
                        "You cannot assign the recursive project dependence %s",
                        rec.project_id.display_name,
                    )
                )

            if rec.project_id:
                self._cr.execute(
                    """select * from 
                    project_product_dependent_rel
                     where product_id != %s and project_id = %s
                     """,
                    (rec.id, rec.project_id.id),
                )
                project_ids = self._cr.dictfetchall()
                for line in project_ids:
                    product_id = line.get("product_id")
                    product_id = self.browse(product_id)
                    if rec.dependent_project_ids.filtered(
                        lambda l: l.id == product_id.project_id.id
                    ):
                        raise ValidationError(
                            _(
                                "You cannot assign the recursive project dependence %s",
                                product_id.display_name,
                            )
                        )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_service_generation(self):
        res = super()._timesheet_service_generation()

        for line in self:
            depend_task = False
            if line.product_id.dependent_project_ids:
                depend_task = self.filtered(
                    lambda l: l.id != line.id
                    and l.product_id.project_id.id
                    in line.product_id.dependent_project_ids.ids
                )
                if depend_task:
                    for task in depend_task:
                        line.task_id.depend_on_ids = [
                            (Command.link(task.mapped("task_id").id))
                        ]

            depend_task = line.order_id.order_line.filtered(
                lambda l: l.id != line.id
                and line.product_id.project_id.id
                in l.product_id.dependent_project_ids.ids
            )
            if depend_task:
                depend_task.task_id.depend_on_ids = [
                    (Command.link(line.mapped("task_id").id))
                ]

        return res
