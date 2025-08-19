import base64

from odoo import api, fields, models


class OperatingCompany(models.Model):
    _name = "operating.company"
    _description = "Operating Company"

    name = fields.Char(
        related="partner_id.name",
        string="Operating Company Name",
        required=True,
        store=True,
        readonly=False,
    )
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    company_details = fields.Html(
        string="Company Details",
        help="Header text displayed at the top of all reports.",
    )
    bank_ids = fields.One2many(related="partner_id.bank_ids", readonly=False)
    country_id = fields.Many2one(
        "res.country",
        compute="_compute_address",
        inverse="_inverse_country",
        string="Country",
    )
    email = fields.Char(related="partner_id.email", store=True, readonly=False)
    phone = fields.Char(related="partner_id.phone", store=True, readonly=False)
    mobile = fields.Char(related="partner_id.mobile", store=True, readonly=False)
    website = fields.Char(related="partner_id.website", readonly=False)
    vat = fields.Char(related="partner_id.vat", string="Tax ID", readonly=False)
    company_registry = fields.Char(
        related="partner_id.company_registry", string="Company ID", readonly=False
    )
    street = fields.Char(compute="_compute_address", inverse="_inverse_street")
    street2 = fields.Char(compute="_compute_address", inverse="_inverse_street2")
    zip = fields.Char(compute="_compute_address", inverse="_inverse_zip")
    city = fields.Char(compute="_compute_address", inverse="_inverse_city")
    state_id = fields.Many2one(
        "res.country.state",
        compute="_compute_address",
        inverse="_inverse_state",
        string="Fed. State",
        domain="[('country_id', '=?', country_id)]",
    )
    logo = fields.Binary(
        related="partner_id.image_1920", string="Company Logo", readonly=False
    )
    stamp = fields.Binary(string="Stamp")

    payment_provider_ids = fields.Many2many(
        "payment.provider",
        string="Payment Provider",
        domain=[
            ("state", "in", ["enabled", "test"]),
        ],
    )

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string="Fiscal Position",
        help="Fiscal positions are used to adapt taxes and accounts for particular customers or sales orders/invoices."
            "The default value comes from the customer.")

    sequence_id = fields.Many2one("ir.sequence", "Operating Sequence", copy=False)
    # bank_account_id = fields.Many2one('res.partner.bank', string="Bank Account")

    _sql_constraints = [
        ("name_uniq", "unique (name)", "The Operating company name must be unique !")
    ]

    def _get_company_address_field_names(self):
        return ["street", "street2", "city", "zip", "state_id", "country_id"]

    def _get_company_address_update(self, partner):
        return dict(
            (fname, partner[fname]) for fname in self._get_company_address_field_names()
        )

    def _compute_address(self):
        for company in self.filtered(lambda company: company.partner_id):
            address_data = company.partner_id.sudo().address_get(adr_pref=["contact"])
            if address_data["contact"]:
                partner = company.partner_id.browse(address_data["contact"]).sudo()
                company.update(company._get_company_address_update(partner))

    def _inverse_street(self):
        for company in self:
            company.partner_id.street = company.street

    def _inverse_street2(self):
        for company in self:
            company.partner_id.street2 = company.street2

    def _inverse_zip(self):
        for company in self:
            company.partner_id.zip = company.zip

    def _inverse_city(self):
        for company in self:
            company.partner_id.city = company.city

    def _inverse_state(self):
        for company in self:
            company.partner_id.state_id = company.state_id

    def _inverse_country(self):
        for company in self:
            company.partner_id.country_id = company.country_id

    @api.depends("partner_id.image_1920")
    def _compute_logo_web(self):
        for company in self:
            img = company.partner_id.image_1920
            company.logo_web = img and base64.b64encode(
                tools.image_process(base64.b64decode(img), size=(180, 0))
            )

    @api.onchange("state_id")
    def _onchange_state(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id

    @api.model_create_multi
    def create(self, vals_list):
        # create missing partners
        no_partner_vals_list = [
            vals
            for vals in vals_list
            if vals.get("name") and not vals.get("partner_id")
        ]
        if no_partner_vals_list:
            partners = self.env["res.partner"].create(
                [
                    {
                        "name": vals["name"],
                        "is_company": True,
                        "image_1920": vals.get("logo"),
                        "email": vals.get("email"),
                        "phone": vals.get("phone"),
                        "website": vals.get("website"),
                        "vat": vals.get("vat"),
                        "country_id": vals.get("country_id"),
                    }
                    for vals in no_partner_vals_list
                ]
            )
            partners.flush_model()
            for vals, partner in zip(no_partner_vals_list, partners):
                vals["partner_id"] = partner.id

        self.clear_caches()

        return super().create(vals_list)

    # @api.model
    # def _search(
    #     self,
    #     args,
    #     offset=0,
    #     limit=None,
    #     order=None,
    #     count=False,
    #     access_rights_uid=None,
    # ):
    #     if self._context.get("is_opc_m2o") and self.env.company.operating_company_ids:
    #         args = [("id", "in", self.env.company.operating_company_ids.ids)]

    #     return super(OperatingCompany, self)._search(
    #         args, offset, limit, order, count=count, access_rights_uid=access_rights_uid
    #     )
