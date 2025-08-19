from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    whatsapp_url = fields.Char(
        string="WhatsApp URL",
        config_parameter="res.config.settings.whatsapp_url"
    )
    whatsapp_token = fields.Char(
        string="WhatsApp Token",
        config_parameter="res.config.settings.whatsapp_token"
    )
    morning_message = fields.Char(
        string="Morning Message",
        config_parameter="res.config.settings.morning_message"
    )
    afternoon_message = fields.Char(
        string="Afternoon Message",
        config_parameter="res.config.settings.afternoon_message"
    )
    evening_message = fields.Char(
        string="Evening Message",
        config_parameter="res.config.settings.evening_message"
    )
    halfday_message = fields.Char(
        string="Halfday Message",
        config_parameter="res.config.settings.halfday_message"
    )
    fullday_message = fields.Char(
        string="Fullday Message",
        config_parameter="res.config.settings.fullday_message"
    )

    # Aggremet Whatsapp Credancials
    ageement_whatsapp_url = fields.Char(string="WhatsApp URL", config_parameter='res.config.settings.ageement_whatsapp_url')
    ageement_whatsapp_token = fields.Char(string="WhatsApp Token", config_parameter='res.config.settings.ageement_whatsapp_token')

    @api.model
    def get_values(self):
        """Retrieve stored values for WhatsApp settings."""
        res = super(ResConfigSettings, self).get_values()
        res.update({
            'whatsapp_url': self.env['ir.config_parameter'].sudo().get_param('res.config.settings.whatsapp_url', default=''),
            'whatsapp_token': self.env['ir.config_parameter'].sudo().get_param('res.config.settings.whatsapp_token', default=''),
            'morning_message': self.env['ir.config_parameter'].sudo().get_param('res.config.settings.morning_message', default=''),
            'afternoon_message': self.env['ir.config_parameter'].sudo().get_param('res.config.settings.afternoon_message', default=''),
            'evening_message': self.env['ir.config_parameter'].sudo().get_param('res.config.settings.evening_message', default=''),
            'halfday_message': self.env['ir.config_parameter'].sudo().get_param('res.config.settings.halfday_message', default=''),
            'fullday_message': self.env['ir.config_parameter'].sudo().get_param('res.config.settings.fullday_message', default=''),
        })
        return res

    def set_values(self):
        """Save the values of WhatsApp settings."""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('res.config.settings.whatsapp_url', self.whatsapp_url or '')
        self.env['ir.config_parameter'].sudo().set_param('res.config.settings.whatsapp_token', self.whatsapp_token or '')
        self.env['ir.config_parameter'].sudo().set_param('res.config.settings.morning_message', self.morning_message or '')
        self.env['ir.config_parameter'].sudo().set_param('res.config.settings.afternoon_message', self.afternoon_message or '')
        self.env['ir.config_parameter'].sudo().set_param('res.config.settings.evening_message', self.evening_message or '')
        self.env['ir.config_parameter'].sudo().set_param('res.config.settings.halfday_message', self.halfday_message or '')
        self.env['ir.config_parameter'].sudo().set_param('res.config.settings.fullday_message', self.fullday_message or '')
