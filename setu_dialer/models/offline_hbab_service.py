from odoo import models, fields, api

class OfflineHbabService(models.Model):
    _name = 'offline.hbab.service'
    _description = 'Offline HBAB Service'
    _rec_name = 'customer_name'
    _order = 'create_date desc'

    customer_name = fields.Char(string="Customer Name", required=True)
    contact_number = fields.Char(string="Contact Number", required=True)

    customer_type = fields.Selection([
        ('new', 'New Customer'),
        ('existing', 'Existing Customer')
    ], string="Customer Type", required=True)

    services_type = fields.Many2one('offline.hbab.status', string="Service Type", required=True)

    @api.model
    def create(self, vals):
        # First create the offline.hbab.service record
        record = super(OfflineHbabService, self).create(vals)

        # Now create a record in hbad.data.info
        self.env['hbad.data.info'].create({
            'customer_name': record.customer_name,
            'contact_number': record.contact_number,
            'customer_type': record.customer_type,
            'services_type': record.services_type.id,
        })

        return record

    def write(self, vals):
        res = super(OfflineHbabService, self).write(vals)

        for rec in self:
            # Search for an existing record in hbad.data.info
            info = self.env['hbad.data.info'].search([
                ('contact_number', '=', rec.contact_number)
            ], limit=1)

            data = {
                'customer_name': rec.customer_name,
                'contact_number': rec.contact_number,
                'customer_type': rec.customer_type,
                'services_type': rec.services_type.id,
            }

            if info:
                info.write(data)
        return res