# -*- coding: utf-8 -*-

from odoo import fields, api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    model_ids = fields.Many2many("ir.model")