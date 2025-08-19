import threading
import random
import string
import odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = "res.partner"

    credentials_ids = fields.One2many("res.partner.credentials", "res_partner_id", string="Credentials")

    @api.constrains('mobile', 'phone')
    def _check_mobile_phone(self):
        """Ensure Mobile and Phone fields contain only 10-digit numbers."""
        for partner in self:
            if partner.mobile and (not partner.mobile.isdigit() or len(partner.mobile) != 10):
                raise ValidationError("Mobile number must be exactly 10 digits and contain only numbers.")

class ResPartnerCredentials(models.Model):
    _name = "res.partner.credentials"
    _description = "Res Partner Credentials"
    _inherit = ['mail.thread', 'mail.activity.mixin'] 

    res_partner_id = fields.Many2one("res.partner", string="Partner")
    link = fields.Char(string="Link")
    user_email = fields.Char(string="User Email")
    phone = fields.Char(string="Phone")
    password = fields.Char(string="Password", default="****", readonly=True)
    actual_password = fields.Char(string="Actual Password", invisible=True)

    def generate_password(self):
        """Generate a secure random password and store it."""
        characters = string.ascii_letters + string.digits + string.punctuation
        new_password = ''.join(random.choices(characters, k=12))
        user = self.env.user

        message_text = _("A new password has been generated.")
        if self.actual_password:
            message_text = _("Password has been re-generated.")

        self.sudo().write({
            'actual_password': new_password,
            'password': '****'
        })

        self.res_partner_id.message_post(
            body=f"User <b>{user.name}</b> generated the password.",
            subject="Password generated",
            message_type="notification"
        )

        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'New password generated successfully!',
                'type': 'rainbow_man',
            }
        }

    def toggle_password_visibility(self):
        user = self.env.user
        """Temporarily show the actual password for 5 seconds, then hide it, and reload the page after 6 seconds."""
        for rec in self:
            if rec.actual_password:
                rec.sudo().write({'password': rec.actual_password})
                self.env.cr.commit()
                # Log in chatter
                rec.res_partner_id.message_post(
                    body=f"User <b>{user.name}</b> viewed the password.",
                    subject="Password Viewed",
                    message_type="notification"
                )
                threading.Timer(5, self._hide_password_thread, args=[rec.id, self.env.registry]).start()

    @staticmethod
    def _hide_password_thread(record_id, registry):
        """Securely hides the password after 5 seconds."""
        with registry.cursor() as cr:
            env = api.Environment(cr, odoo.SUPERUSER_ID, {})
            record = env["res.partner.credentials"].browse(record_id)
            if record.exists():
                record.sudo().write({'password': '****'})
                cr.commit()