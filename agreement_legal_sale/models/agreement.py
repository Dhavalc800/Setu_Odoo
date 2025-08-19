# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Agreement(models.Model):
    _inherit = "agreement"

    sale_id = fields.Many2one("sale.order", string="Sales Order")
    salesperson = fields.Many2one('res.users',string='SalesPerson', related="sale_id.user_id")
    booking_type = fields.Selection(related="sale_id.booking_type", store=True,)


class AgreementLine(models.Model):
    _inherit = "agreement.line"

    sale_line_id = fields.Many2one("sale.order.line", string="Sales Order Line")


class ProjectTask(models.Model):
    _inherit="project.task"

    booking_type = fields.Selection(related="sale_order_id.booking_type", store=True,)
