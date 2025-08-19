from odoo import models, fields, api, SUPERUSER_ID
from datetime import datetime, date

class ResUsers(models.Model):
    _inherit = 'res.users'

    x_user_lead_id = fields.Many2one('lead.data.lead', string="User Current Lead")
    daily_lead_fetch_count = fields.Integer(
        string="Leads Fetched Today",
        compute="_compute_daily_lead_fetch_count"
    )

    # @classmethod
    # def _login(cls, db, login, password, *, user_agent_env=None):
    #     """Case-insensitive login."""
    #     login = login.lower().strip()
        
    #     # Get the environment
    #     with cls.pool.cursor() as cr:
    #         env = api.Environment(cr, SUPERUSER_ID, {})
            
    #         # Search for user with case-insensitive login
    #         user = env['res.users'].search([
    #             ('login', '=ilike', login),
    #             ('active', '=', True)
    #         ], limit=1)
            
    #         if user:
    #             # Update the login to lowercase for consistency
    #             user.login = login
    #             cr.commit()
        
    #     return super()._login(db, login, password, user_agent_env=user_agent_env)

    def _compute_daily_lead_fetch_count(self):
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        Lead = self.env['lead.data.lead']

        for user in self:
            # Try getting campaign from context (only available in campaigns view)
            campaign_id = self.env.context.get('active_id')
            
            domain = [
                ('is_fetch', '=', True),
                ('fetch_user_id', '=', user.id),
                ('fetch_date', '>=', today_start),
                ('fetch_date', '<=', today_end),
            ]
            if campaign_id:
                domain.append(('campaign_id', '=', campaign_id))

            user.daily_lead_fetch_count = Lead.search_count(domain)



