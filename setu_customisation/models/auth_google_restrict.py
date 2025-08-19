from odoo import models, _, api
from odoo.exceptions import AccessDenied
import logging

_logger = logging.getLogger(__name__)

class AuthOauth(models.Model):
    _inherit = 'auth.oauth.provider'

    def _auth_oauth_validate(self, provider, access_token, extra_data):
        """Override to restrict login to allowed domains."""
        _logger.info("Google Login: Checking email domain restriction...")

        res = super()._auth_oauth_validate(provider, access_token, extra_data)

        allowed_domains = ["setu.co.in", "vardan.co.in"]
        email = res.get("email", "")
        domain = email.split("@")[-1] if "@" in email else ""

        _logger.info(f"User email: {email}, Extracted domain: {domain}")

        if domain not in allowed_domains:
            raise AccessDenied(_("You do not have access to this database. Only emails from setu.co.in and vardan.co.in are allowed."))

        return res
