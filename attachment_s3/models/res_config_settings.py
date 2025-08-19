from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    aws3_region_name = fields.Char(string="AWS Region Name")
    aws3_access_key = fields.Char(string="AWS Access Key")
    aws3_secret_key = fields.Char(string="AWS Secret Key")
    aws3_bucket_name = fields.Char(string="AWS Bucket Name")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        aws3_region_name = params.get_param("aws3_region_name", False)
        aws3_access_key = params.get_param("aws3_access_key", False)
        aws3_secret_key = params.get_param("aws3_secret_key", False)
        aws3_bucket_name = params.get_param("aws3_bucket_name", False)
        res.update(
            aws3_region_name=aws3_region_name,
            aws3_access_key=aws3_access_key,
            aws3_secret_key=aws3_secret_key,
            aws3_bucket_name=aws3_bucket_name,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "aws3_region_name", self.aws3_region_name
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "aws3_access_key", self.aws3_access_key
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "aws3_secret_key", self.aws3_secret_key
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "aws3_bucket_name", self.aws3_bucket_name
        )
