from odoo import api, fields, models

class CampaignsList(models.Model):
    _name = 'closer.name'
    _description = "closer_name"
    _order = 'create_date desc'
    _rec_name = 'closer_id'

    closer_id = fields.Many2one('hr.employee', string="Cloaser")
    user_id = fields.Many2one('res.users', string="User", compute='_compute_user_id', store=True)

    @api.depends('closer_id')
    def _compute_user_id(self):
        for record in self:
            record.user_id = record.closer_id.user_id if record.closer_id else False
