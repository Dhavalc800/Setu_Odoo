from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    pre_sales_percentage = fields.Integer(
        string="Percentage",
        config_parameter="scs_pre_salesperson.pre_sales_percentage"
    )
