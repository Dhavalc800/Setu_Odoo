from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AgreementStage(models.Model):
    _inherit = 'agreement.stage'

    is_active = fields.Boolean(string='Is Active')
    agreement_type_id = fields.Many2one("agreement.type", string="Type")

    # @api.constrains('is_active')
    # def check_is_active(self):
    #     for stage in self:
    #         if stage.is_active:
    #             # Check if there is another active stage
    #             other_active_stages = self.search([('id', '!=', stage.id), ('is_active', '=', True)])
    #             if other_active_stages:
    #                 raise ValidationError('Only one stage can be active at a time.')
