from odoo import models, fields, api

class HbadDataInfo(models.Model):
    _name = 'hbad.data.info'
    _description = 'HBAD Data Info'
    _rec_name = 'booking_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    date = fields.Date(string="Date")
    booking_id = fields.Char(string="Booking ID")
    allocation_date = fields.Date(string="Allocation Date")
    contact_number = fields.Char(string="Contact Number")
    customer_name = fields.Char(string="Customer Name")
    structure = fields.Char(string="Structure")
    product_ids = fields.Many2many('product.template', string="Products")
    location = fields.Char(string="Location")
    status = fields.Many2one('hbab.data.status', string="Status")
    remarks = fields.Text(string="Remarks")
    brief = fields.Text(string="Brief")

    customer_type = fields.Selection([
        ('new', 'New Customer'),
        ('existing', 'Existing Customer')
    ], string="Customer Type", required=True)

    services_type = fields.Many2one('offline.hbab.status', string="Service Type", required=True)
