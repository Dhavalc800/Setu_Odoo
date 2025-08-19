from odoo import api, fields, models, _


class ReportColumn(models.Model):
    _name = 'report.column'
    _description = "Report Column"

    name = fields.Char(string="Column Name")