import re
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError



class Partner(models.Model):
    _inherit = "res.partner"

    proprietorship_type = fields.Selection(
        [
            ("private_ltd", "Private Limited"),
            ("limited", "Limited"),
            ("foundation", "Foundation"),
            ("llp", "LLP"),
            ("partnership", "Partnership"),
            ("sole", "Sole Proprietorship"),
        ]
    )
    cinn = fields.Char("CIN Number")
    llp_no = fields.Char("LLP Number")
    firm_no = fields.Char("Firm Number")
    msme_number = fields.Char("MSME Udhyam Number")
    incorporation_date = fields.Date("Incorporation Date", tracking=True)
    sector_id = fields.Many2one("industry.sector", "Sector")
    hide_ca_number = fields.Boolean("Hide CA Number", compute="_compute_hide_ca_mobile_number")
    hide_mobile = fields.Boolean("Hide Mobile", compute="_compute_hide_ca_mobile_number")
    mobile = fields.Char(unaccent=False, tracking=True)
    l10n_in_gst_treatment = fields.Selection([
            ('regular', 'Registered Business - Regular'),
            ('composition', 'Registered Business - Composition'),
            ('unregistered', 'Unregistered Business'),
            ('consumer', 'Consumer'),
            ('overseas', 'Overseas'),
            ('special_economic_zone', 'Special Economic Zone'),
            ('deemed_export', 'Deemed Export'),
            ('uin_holders', 'UIN Holders'),
        ], string="GST Treatment", tracking=True)
    l10n_in_pan = fields.Char(string="PAN", help="""PAN enables the department to link all transactions of the person with the department.
                                These transactions include taxpayments, TDS/TCS credits, returns of income/wealth/gift/FBT, specified transactions, correspondence, and so on.
                                thus, PAN acts as an identifier for the person with the tax department.""", tracking=True)
    street = fields.Char(tracking=True)
    street2 = fields.Char(tracking=True)
    city = fields.Char(tracking=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]", tracking=True)
    zip = fields.Char(change_default=True)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', tracking=True)
    zip = fields.Char(change_default=True, tracking=True)


    def _compute_hide_ca_mobile_number(self):
        for record in self:
            record.hide_ca_number = self.user_has_groups("scs_sale.group_hide_ca_number")
            record.hide_mobile = self.user_has_groups("scs_sale.group_hide_mobile_number")

    @api.constrains("cinn")
    def _check_corporate_identification(self):
        for record in self.filtered(lambda l: l.cinn):
            if not self.isValid_CIN_Number(record.cinn):
                raise ValidationError(
                    _("Corporate Identification Number (CIN) is invalid!!"),
                )

    def isValid_CIN_Number(self, str):
        regex = "([LUu]{1})([0-9]{5})([A-Za-z]{2})([0-9]{4})([A-Za-z]{3})([0-9]{6})$"
        p = re.compile(regex)
        return True if re.search(p, str) else False

    @api.onchange("industry_id")
    def onchange_industry(self):
        self.sector_id = False

    @api.onchange("company_type")
    def onchange_company_type(self):
        res = super().onchange_company_type()
        if self.company_type == "person":
            self.cinn = (
                self.llp_no
            ) = (
                self.proprietorship_type
            ) = self.firm_no = self.msme_number = self.incorporation_date = False
        return res
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self.user_has_groups('sales_team.group_sale_salesman') and not\
                self.user_has_groups('sales_team_security.group_sale_team_manager') and not\
                self.user_has_groups('sales_team.group_sale_salesman_all_leads') and not\
                self.user_has_groups('sales_team.group_sale_manager'):
            args += [('user_id', '=', self.env.user.id), ('user_id', '!=', False)]
        return super(Partner, self)._search(args, offset=offset, limit=limit, order=order, count=count,
                                                      access_rights_uid=access_rights_uid)

    @api.depends('parent_id')
    def _compute_user_id(self):
        super()._compute_user_id()
        if not self.user_id:
            self.user_id = self.env.user.id
