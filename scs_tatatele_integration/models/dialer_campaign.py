from odoo import fields, models, api


class DailerCampaign(models.Model):
    _name = 'dialer.campaign'
    _description = 'Dailer Campaign'

    campaign_id = fields.Char("Campaign ID", required=True)
    name = fields.Char("Name", required=True)


class CampaingDetails(models.Model):
    _name = 'campaign.details'
    _description = 'Campaign Details'

    name = fields.Char("Name")
    campaignId = fields.Char("CampaignId", required=True)
    description = fields.Char('Description')
    auto_dial_duration = fields.Char("Auto Dial Duration")
    user_ids = fields.One2many('res.users', 'campaign_details_id', "Agents")
