# -*- coding: utf-8 -*-
from odoo import fields, models, api


class FundingServiceMonth(models.Model):
    _name = "funding.service.month"

    name = fields.Char(string="Month Name")
    month_number = fields.Integer(string="Month Number")