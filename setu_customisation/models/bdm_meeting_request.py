from odoo import models, fields, api
from odoo.exceptions import UserError

class BdmMeetingRequest(models.Model):
    _name = 'bdm.meeting.request'
    _description = 'BDM Physical Meeting Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users', string='BDM', default=lambda self: self.env.user, tracking=True)
    with_user_id = fields.Many2one('res.users', string='With Person', tracking=True)
    city = fields.Char(string='City', tracking=True)
    area = fields.Char(string='Area', tracking=True)
    address = fields.Text(string='Address', tracking=True)
    start_date = fields.Date(string='Start Date', tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    branch_manager_id = fields.Many2one('hr.employee', string='Branch Manager', tracking=True)
    bdm_state = fields.Selection([
        ('requested', 'Requested to BM'),
    ], string='BDM Status', default=False, tracking=True)

    bm_state = fields.Selection([
        ('approved', 'Approved by BM'),
        ('rejected', 'Rejected by BM'),
    ], string='BM Status', default=False, tracking=True)
    bdm_remark = fields.Text(string="BDM Remark")
    bm_remark = fields.Text(string="BM Remark")

    def action_send_request(self):
        for rec in self:
            rec.bdm_state = 'requested'

    def action_approve(self):
        for rec in self:
            rec.bm_state = 'approved'

    def action_reject(self):
        for rec in self:
            rec.bm_state = 'rejected'
