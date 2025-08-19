from odoo import models, fields, api

class Employee(models.Model):
    _inherit = 'hr.employee'

    hold = fields.Boolean(string="On Hold", default=False)
    is_send_msg = fields.Boolean(string="Send Message", default=True)

    def action_set_hold(self):
        """Mark selected employees as on hold"""
        for record in self:
            record.hold = True

    def action_unset_hold(self):
        """Remove hold status from selected employees"""
        for record in self:
            record.hold = False

    @api.model
    def remove_employee_images(self):
        employees = self.search([('image_1920', '!=', False)])
        for employee in employees:
            print("\n\n\nRemoving image_1920 for employee:",employee.name)
            employee.image_1920 = False
        _logger = self.env['ir.logging']
        _logger.sudo().create({
            'name': 'Image Cleaner',
            'type': 'server',
            'level': 'info',
            'dbname': self.env.cr.dbname,
            'message': f'Removed image_1920 from {len(employees)} employees.',
            'path': 'hr.employee',
            'func': 'remove_employee_images',
            'line': 0,
        })