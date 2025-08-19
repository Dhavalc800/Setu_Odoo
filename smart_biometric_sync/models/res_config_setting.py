from odoo import models, fields, api
from datetime import date, timedelta

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_key = fields.Char(string="API Key")
    api_url = fields.Char(string="API URL")
    from_date = fields.Date(string="From Date", default=lambda self: self._default_from_date())
    to_date = fields.Date(string="To Date", default=lambda self: self._default_to_date())

    @api.model
    def _default_from_date(self):
        """Returns today's date as default from_date."""
        return date.today()

    @api.model
    def _default_to_date(self):
        """Returns today's date as default to_date."""
        return date.today()

    @api.model
    def get_values(self):
        """Retrieve stored values or set defaults."""
        res = super(ResConfigSettings, self).get_values()
        res.update(
            api_key=self.env['ir.config_parameter'].sudo().get_param('hr_attendance.api_key'),
            api_url=self.env['ir.config_parameter'].sudo().get_param('hr_attendance.api_url'),
            from_date=self.env['ir.config_parameter'].sudo().get_param('hr_attendance.from_date') or self._default_from_date(),
            to_date=self.env['ir.config_parameter'].sudo().get_param('hr_attendance.to_date') or self._default_to_date(),
        )
        return res

    def set_values(self):
        """Store values when saving settings."""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('hr_attendance.api_key', self.api_key)
        self.env['ir.config_parameter'].sudo().set_param('hr_attendance.api_url', self.api_url)
        self.env['ir.config_parameter'].sudo().set_param('hr_attendance.from_date', self.from_date)
        self.env['ir.config_parameter'].sudo().set_param('hr_attendance.to_date', self.to_date)

    @api.model
    def update_dates_daily(self):
        """Cron job function to update from_date and to_date automatically every day."""
        self.env['ir.config_parameter'].sudo().set_param('hr_attendance.from_date', str(date.today()))
        self.env['ir.config_parameter'].sudo().set_param('hr_attendance.to_date', str(date.today()))

