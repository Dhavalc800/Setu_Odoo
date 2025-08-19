from odoo import fields, models, api, _, registry, SUPERUSER_ID
from odoo.exceptions import ValidationError


class UserToken(models.TransientModel):
    _name = 'user.token'
    _description = "User Token"
    _rec_name = "user_email"

    user_email = fields.Char(string="User Email")
    user_password = fields.Char(string="User Password")
    token_generated = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Token Generated")
    generate_user_token = fields.Boolean(string="Token Generated")

    def generate_token(self):
        for rec in self:
            if not (rec.user_email or rec.user_password):
                raise ValidationError(_("Please Enter both Email and Password to generate access token"))
            self.env.user.tata_email = self.user_email
            self.env.user.tata_password = self.user_password
            self.env.user.generate_access_token()
            notify = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Your access token has generated successfully'),
                    'sticky': False,
                }
            }
            return notify
