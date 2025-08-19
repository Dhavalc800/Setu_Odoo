from odoo import fields, models


class TimesheetRefuseReason(models.TransientModel):
    '''This TransientModel create the Refuse Reason in the timesheet '''
    
    _name = "timesheet.refuse.reason"
    _description = "Timesheet Refuse Reason Wizard"

    name = fields.Char(string='Refuse Reason', required=True)

    
    def timesheet_refuse_reason(self):
        '''This is method is use to set the Refuse Reason in the timesheet '''
        
        employee_active_id= self.env.context.get('active_ids', [])[0]
        get_timesheet_id = self.env['hr_timesheet.sheet'].search([('id','=',employee_active_id)])
        new_vals={'refuse_reason': self.name, "state": "draft", "reviewer_id": False}
        get_timesheet_id.write(new_vals)

