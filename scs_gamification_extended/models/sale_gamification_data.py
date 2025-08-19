from odoo import fields, models


class SaleGamificationData(models.Model):
    _name = "sale.gamification.data"
    _description = "Sale Gamification Data"
    _rec_name = 'salesperson_id'

    salesperson_id = fields.Many2one("res.users", string="Salesperson", tracking=True)
    percentage = fields.Float("Percentage in %", tracking=True)
    order_id = fields.Many2one("sale.order", tracking=True)
