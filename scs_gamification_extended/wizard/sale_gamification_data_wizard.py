from odoo import fields, models


class SaleGamificationDataWizard(models.TransientModel):
    _name = "sale.gamification.data.wizard"
    _description = "Add Sels persion percentage"

    salesperson_id = fields.Many2one('res.users', "Salesperson", required=True)
    percentage = fields.Float("Percentage in %") 
    wizard_id = fields.Many2one('gamification.data.wizard', "Wizard")
