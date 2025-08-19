from odoo import fields, models


class SalePersonTargetLine(models.Model):
    _name = "sale.person.target.line"
    _description = "Sale Person Target Line"

    user_id = fields.Many2one("res.users", "User", required=True)
    employee_id = fields.Many2one(related="user_id.employee_id", string="Employee")
    amount = fields.Float("Target Amount")
    sale_person_target_id = fields.Many2one("sale.person.target", "Sale Person Target")
