from odoo import models, fields, api
from datetime import datetime, date

class DashboardOverview(models.TransientModel):
    _name = 'dashboard.overview'
    _description = 'Dashboard Overview'

    name = fields.Char('Name')
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    employee_id = fields.Many2one(related="user_id.employee_id", string="Employee")
    manager_id = fields.Many2one(related="employee_id.parent_id", string="Manager Id")
    intro_count = fields.Integer(string='Intro Count', compute="_compute_overview_metrics", store=True)
    prospect_count = fields.Integer(string='Prospect Count', compute="_compute_overview_metrics", store=True)
    expected_revenue_total = fields.Float(string='Expected Revenue Total', compute="_compute_overview_metrics", store=True)
    talk_time_average = fields.Float(string='Talk Time Average', compute="_compute_overview_metrics", store=True)
        
    # For time off requests (you might want to link to existing HR module or create your own)
    overview_line_ids = fields.One2many('dashboard.overview.line', 'dashboard_id', string='Time Off Requests')

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, ''))  # Return empty string as display name
        return result

    @api.model
    def default_get(self, field_names):
        res = super(DashboardOverview, self).default_get(field_names)
        self.action_update_dashboard_lines()
        return res

    def action_update_dashboard_lines(self):
        today = date.today()
        for rec in self:
            rec.overview_line_ids.unlink()

            domain = [
                ('call_datetime', '>=', datetime.combine(today, datetime.min.time())),
                ('call_datetime', '<=', datetime.combine(today, datetime.max.time())),
            ]

            if not self.user_has_groups('sales_team.group_sale_manager'):
                if self.user_has_groups('sales_team_security.group_booking_branch_manager'):
                    teams = self.env['crm.team'].search([('branch_manager_id', '=', self.env.user.id)])
                    team_member_ids = teams.mapped('member_ids').ids
                    domain.append(('user_id', 'in', team_member_ids + [self.env.uid]))
                else:
                    domain.append(('user_id', '=', self.env.uid))

            histories = self.env['lead.call.merged'].search(domain)
            lines = []

            for h in histories:
                disposition_name = (h.disposition_id.name or "").lower()
                if 'intro' in disposition_name or 'prospect' in disposition_name:
                    lines.append((0, 0, {
                        'user_id': h.user_id.id,
                        'lead_id': h.lead_id.id,
                        'disposition_id': h.disposition_id.id,
                        'opportunity_name': h.opportunity_name,
                        'expected_revenue': float(h.expected_revenue or 0),
                        # 'tack_time': h.call_time or '00:00:00'
                    }))

            rec.overview_line_ids = lines


    # def action_update_dashboard_lines(self):
    #     today = date.today()
    #     for rec in self:
    #         rec.overview_line_ids.unlink()

    #         domain = [
    #             ('call_time', '>=', datetime.combine(today, datetime.min.time())),
    #             ('call_time', '<=', datetime.combine(today, datetime.max.time())),
    #         ]

    #         if not self.user_has_groups('sales_team.group_sale_manager'):
    #             if self.user_has_groups('sales_team_security.group_booking_branch_manager'):
    #                 # Fetch all teams where the current user is the branch manager
    #                 teams = self.env['crm.team'].search([('branch_manager_id', '=', self.env.user.id)])
    #                 team_member_ids = teams.mapped('member_ids').ids
    #                 domain.append(('user_id', 'in', team_member_ids + [self.env.uid]))
    #             else:
    #                 domain.append(('user_id', '=', self.env.uid))

    #         histories = self.env['lead.call.merged'].search(domain)
    #         lines = []

    #         for h in histories:
    #             lines.append((0, 0, {
    #                 'user_id': h.user_id.id,
    #                 'lead_id': h.lead_id.id,
    #                 'disposition_id': h.disposition_id.id,
    #                 'opportunity_name': h.opportunity_name,
    #                 'expected_revenue': float(h.expected_revenue or 0),
    #                 'tack_time': h.call_time or '00:00:00'
    #             }))

    #         rec.overview_line_ids = lines


    @api.depends('overview_line_ids')
    def _compute_overview_metrics(self):
        for rec in self:
            intro_count = prospect_count = total_expected = total_seconds = 0
            talk_time_count = 0
            
            for line in rec.overview_line_ids:
                if line.disposition_id.name:
                    if 'INTRO' in line.disposition_id.name:
                        intro_count += 1
                    if 'Prospect' in line.disposition_id.name:
                        prospect_count += 1
                
                total_expected += line.expected_revenue
                
                if line.tack_time:
                    try:
                        h, m, s = map(int, line.tack_time.split(':'))
                        total_seconds += h * 3600 + m * 60 + s
                        talk_time_count += 1
                    except ValueError:
                        continue
            
            rec.update({
                'intro_count': intro_count,
                'prospect_count': prospect_count,
                'expected_revenue_total': total_expected,
                'talk_time_average': round(total_seconds / talk_time_count / 60, 2) if talk_time_count else 0.0,
            })


class DashboardOverviewLine(models.TransientModel):
    _name = 'dashboard.overview.line'
    _description = 'Dashboard Overview Line'

    dashboard_id = fields.Many2one('dashboard.overview', string='Dashboard')
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    lead_id = fields.Many2one('lead.data.lead', string="Lead")
    disposition_id = fields.Many2one('dispo.list.name', string="Select Disposition")
    opportunity_name = fields.Char(string="Opportunity Name")
    expected_revenue = fields.Float(string="Expected Revenue")
    tack_time = fields.Char(string="Talk Time")