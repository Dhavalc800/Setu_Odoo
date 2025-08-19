from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PaymentPlan(models.Model):
    _name = "payment.plan"
    _description = "Payment Plan"

    name = fields.Char(required=True)

    line_ids = fields.One2many("payment.plan.line", "payment_id")

    @api.constrains("line_ids")
    def _check_line_ids(self):
        if sum(self.line_ids.mapped("percentage")) > 100:
            raise ValidationError(
                _("Ensure that the cumulative percentage does not exceed 100%.")
            )


class PaymentPlanLine(models.Model):
    _name = "payment.plan.line"
    _description = "Payment Plan Line"

    state = fields.Char(string="Stage")
    percentage = fields.Float()
    payment_id = fields.Many2one("payment.plan")
    is_advance = fields.Boolean("Advance Payment")

    @api.constrains("percentage", 'is_advance')
    def _check_percentage_is_advance(self):
        for rec in self:
            if not (0 < rec.percentage <= 100):
                raise ValidationError(
                    _("Ensure that the percentage does not exceed 100%.")
                )
            
            if rec.is_advance and self.search(
                [
                    ("is_advance", "=", True),
                    ("id", "!=", rec.id),
                    ("payment_id", "=", rec.payment_id.id),
                ]
            ):
                raise ValidationError(_("Advance Payment already set"))
