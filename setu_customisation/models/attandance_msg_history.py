from odoo import models, fields, api

class AttandanceMsgHistory(models.Model):
    _name = "attandance.msg.history"

    name = fields.Char(string="Employee Name")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    message_date = fields.Date(string="Message Date", default=fields.Date.today)
    message_content = fields.Text(string="Message Content")
    message_type = fields.Selection([
        ('morning', 'Morning Check-in'),
        ('afternoon', 'Afternoon Half-Day Warning'),
        ('evening', 'Evening Checkout Reminder')
    ], string="Message Type")
    half_day = fields.Boolean(string="Half-Day Leave Assigned", default=False)
    full_day = fields.Boolean(string="Full-Day Leave Assigned", default=False)
