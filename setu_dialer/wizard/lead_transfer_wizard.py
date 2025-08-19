from odoo import models, fields, api
from odoo.exceptions import ValidationError

class LeadTransferWizard(models.TransientModel):
    _name = 'lead.transfer.wizard'
    _description = 'Transfer Manual Leads from one employee to another'

    from_employee_id = fields.Many2one('res.users', string="From Employee", required=True)
    to_employee_id = fields.Many2one('res.users', string="To Employee", required=True)
    lead_ids = fields.Many2many('lean.manual.lead', string="Leads to Transfer")

    @api.onchange('from_employee_id')
    def _onchange_from_employee_id(self):
        if self.from_employee_id:
            self.lead_ids = self.env['lean.manual.lead'].search([
                ('employee_id', '=', self.from_employee_id.id)
            ])
        else:
            self.lead_ids = [(5, 0, 0)]

    def action_transfer_leads(self):
        if not self.to_employee_id:
            raise ValidationError("Please select the target employee.")
        for lead in self.lead_ids:
            lead.employee_id = self.to_employee_id.id
        return {'type': 'ir.actions.act_window_close'}
