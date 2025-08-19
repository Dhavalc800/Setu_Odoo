from odoo import models, fields, _
from odoo.exceptions import UserError

class ProjectTask(models.Model):
    _inherit = 'project.task'

    incorporation_date = fields.Date(string="Incorporation Date")

    # def write(self, vals):
    #     if 'active' in vals:
    #         if vals['active'] is True:
    #             if not self.sale_order_id.agreement_id.stage_id[0].is_active:
    #                 raise UserError("You cannot unarchive the task because the associated agreement stage is not active.")                    
        
    #     return super(ProjectTask, self).write(vals)