from odoo import api, fields, models


class CancelReason(models.Model):
    _name = 'cancel.reason'

    name = fields.Char(string="Cancel Reason")
