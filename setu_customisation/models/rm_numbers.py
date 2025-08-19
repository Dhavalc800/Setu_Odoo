from odoo import models, fields, api

class RmNumbers(models.Model):
    _name = 'rm.numbers'

    name = fields.Char(string="Name")
    phone = fields.Char(string="Phone")

    @api.model
    def name_get(self):
        result = []
        for record in self:
            display_name = f"{record.name} - {record.phone}" if record.phone else record.name
            result.append((record.id, display_name))
        return result