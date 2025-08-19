# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import Warning


class ResCompany(models.Model):

    _inherit = 'res.company'

    default_password = fields.Char('Default Password',
                                   help="""This will be used as a
                                   default password when a \
                                   user created """)

    hr_team_ids = fields.Many2many('res.users', 'user_cmp_rel', 'user_id',
                                   'cmp_id', 'HR Team',
                                   copy=False,
                                   help='This field depicts the HR team \
                                    which will be notified \
                                    when HR transactions happen.')

    md_team_ids = fields.Many2many('res.users', 'user_cmp_md_rel', 'user_id',
                                   'cmp_id', string="MD",
                                   copy=False,
                                   help='This field depicts the MD \
                                    which will be notified \
                                    when MD transactions happen.')
    
class ResUsers(models.Model):

    _inherit = 'res.users'

    def update_user_default_password(self):
        for rec in self:
            rec.password = rec.company_id.default_password

    @api.model_create_multi
    def create(self, vals_list):
        company_obj = self.env['res.company']
        for vals in vals_list:
            if vals.get('company_id', False):
                company_id = company_obj.browse(vals.get('company_id'))
                vals.update({"password": company_id.default_password})
        return super().create(vals_list)


    def unlink(self):
        logged_user = self.env.user
        if logged_user.id != SUPERUSER_ID \
                and not logged_user.has_group('hr.group_hr_manager'):
            raise Warning(
                _("You do not have enough access to delete the user !"))
        return super(ResUsers, self).unlink()


class ResGroups(models.Model):

    _inherit = 'res.groups'

    def delete_all_users(self):
        for rec in self:
            rec.users = False
