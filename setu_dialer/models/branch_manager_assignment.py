from odoo import models, fields, api

class BranchManagerAssignment(models.Model):
    _name = 'branch.manager.assignment'
    _description = 'Branch Manager Assignment'
    _rec_name = "lead_id"

    lead_id = fields.Many2one('lead.data.lead', string='Lead')
    source = fields.Char(string='Source')
    phone = fields.Char(string='Phone')
    disposition_id = fields.Many2one('dispo.list.name', string='Disposition')
    call_by = fields.Many2one('res.users', string='Called By', default=lambda self: self.env.user)
    opportunity_name = fields.Char(string='Opportunity')
    expected_revenue = fields.Float(string='Expected Revenue')
    service = fields.Char(string='Service')
    call_date_time = fields.Datetime(string='Call Date & Time', default=fields.Datetime.now)
    branch_manager_id = fields.Many2one('res.users', string='Branch Manager')
    team_id = fields.Many2one('crm.team', string='Sales Team')
    closer_id = fields.Many2one('closer.name', string="Closer")
    member_ids = fields.Many2many('res.users', string='Team Members', compute='_compute_member_ids', store=True)

    @api.depends('team_id')
    def _compute_member_ids(self):
        for record in self:
            record.member_ids = record.team_id.member_ids if record.team_id else False

    @api.onchange('branch_manager_id')
    def _onchange_branch_manager_id(self):
        user = self.env.user

        if self.branch_manager_id:
            # Get all teams where this user is team leader (user_id)
            teams = self.env['crm.team'].search([('user_id', '=', self.branch_manager_id.id)])
            if teams:
                self.team_id = teams[0]  # Set the first team as default
                user.sale_team_id = teams[0]
    
    def action_open_assign_colser_wizard(self):
        """ Open wizard with selected assignments """
        return {
            'name': 'Assign Lead to Closer',
            'type': 'ir.actions.act_window',
            'res_model': 'assign.closer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_assignment_ids': [(6, 0, self.ids)],
                'active_ids': self.ids,
                'active_model': 'branch.manager.assignment',
            },
        }