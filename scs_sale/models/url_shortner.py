from odoo import models, fields
import string
import random
import datetime
from datetime import datetime
import logging
from dateutil import relativedelta
import psycopg2
_logger = logging.getLogger(__name__)


class URLShortener(models.Model):
    _name = 'url.shortener'
    _description = 'URL Shortener'

    long_url = fields.Char(string="Long URL", required=True)
    short_code = fields.Char(string="Short Code", required=True,
                             default=lambda self: self._generate_short_code())

    def _generate_short_code(self, length=6):
        chars = string.ascii_letters + string.digits
        url = ''.join(random.choice(chars) for _ in range(length))
        return url

    def generate_short_url(self):
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        return f"{base_url}/booking-payment/{self.short_code}"

    def clear_short_urls(self):
        urls = self
        if not urls:
            retry_limit_date = datetime.now() - relativedelta.relativedelta(days=2)

            urls = self.search([
                ('create_date', '<=', retry_limit_date.replace(microsecond=0)),
            ])
            for url in urls:
                try:
                    url._clear_all_old_urls()
                    self.env.cr.commit()
                except psycopg2.OperationalError:
                    self.env.cr.rollback()
                except Exception as e:
                    _logger.exception(
                        "encountered an error while clearing draft transaction with reference %s:\n%s",
                        url.id, e
                    )
                    self.env.cr.rollback()

    def _clear_all_old_urls(self):
        self.unlink()
