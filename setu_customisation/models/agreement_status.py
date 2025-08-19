from odoo import models, fields, api

class AgreementStatus(models.Model):
    _name = "agreement.status"

    name = fields.Char(string="Status Name", required=True)