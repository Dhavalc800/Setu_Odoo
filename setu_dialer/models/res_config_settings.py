from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mysql_host = fields.Char(string="MySQL Host", config_parameter='external_db.mysql_host')
    mysql_user = fields.Char(string="MySQL User", config_parameter='external_db.mysql_user')
    mysql_password = fields.Char(string="MySQL Password", config_parameter='external_db.mysql_password')
    mysql_database = fields.Char(string="MySQL Database", config_parameter='external_db.mysql_database')
    mysql_checker = fields.Boolean(string="MySQL Checker", config_parameter="external_db.mysql_checker")