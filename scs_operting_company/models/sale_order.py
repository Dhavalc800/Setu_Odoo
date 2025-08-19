from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # @api.model
    # def _default_operating_company_id(self):
    #     return self.env.company.operating_company_ids and self.env.company.operating_company_ids[0].id
    @api.model
    def default_get(self, fields_list):
        """Call `_compute_operating_companies` when creating a new record."""
        defaults = super().default_get(fields_list)

        # Simulate `user_id` onchange behavior in `default_get`
        if "user_id" in fields_list:
            user = self.env.user
            branch_company = self.env["employee.branch"].search([
                ("name", "=", user.employee_id.branch_id.name)
            ], limit=1)

            if branch_company:
                defaults["operating_company_ids"] = [(6, 0, branch_company.company_ids.ids)]
            else:
                defaults["operating_company_ids"] = [(5, 0, 0)]

        return defaults

    @api.onchange('user_id', 'operating_company_id')
    def _compute_operating_companies(self):
        """Update operating_company_ids based on user_id's branch"""
        branch_company = self.env['employee.branch'].search([
            ('name', '=', self.env.user.employee_id.branch_id.name)
        ], limit=1)
        if branch_company:
            self.operating_company_ids = [(6, 0, branch_company.company_ids.ids)]
        else:
            self.operating_company_ids = [(5, 0, 0)]
        
    operating_company_id = fields.Many2one(
        "operating.company",
        string="Operating Company",
        copy=False
    )

    operating_company_ids = fields.Many2many(
        'operating.company',
        string="Available Operating Companies",
        compute="_compute_operating_companies",
        store=True
    )
    payment_received_amount = fields.Monetary(
        string="Payment Received",
        compute="_compute_get_payment_received",
        compute_sudo=True,
        group_operator="sum",
        store=True,
        # readonly=False,
    )
    payment_pending = fields.Monetary(
        string="Payment Pending",
        compute="_compute_get_payment_recieved_amount",
        compute_sudo=True,
        store=True,
    )

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        if self.operating_company_id:
            vals.update(
                {
                    "operating_company_id": self.operating_company_id.id,
                }
            )
        return vals

    @api.depends("invoice_ids.amount_residual")
    def _compute_get_payment_recieved_amount(self):
        for order in self:
            payment_received = 0
            invoices = order.order_line.invoice_lines.move_id.filtered(
                lambda r: r.move_type == "out_invoice"
            )
            for invoice in invoices:
                if invoice.invoice_payments_widget:
                    payment_content = invoice.invoice_payments_widget.get("content", [])
                    payment_received += sum(
                        value.get("amount", 0) for value in payment_content
                    )
            order.payment_pending = order.amount_total - payment_received

    @api.depends("invoice_ids.amount_residual")
    def _compute_get_payment_received(self):
        for order in self:
            payment_received = 0
            invoices = order.order_line.invoice_lines.move_id.filtered(
                lambda r: r.move_type == "out_invoice"
            )
            for invoice in invoices:
                if invoice.invoice_payments_widget:
                    payment_content = invoice.invoice_payments_widget.get("content", [])
                    payment_received += sum(
                        value.get("amount", 0) for value in payment_content
                    )
            order.payment_received_amount = payment_received

    @api.onchange('partner_id', 'operating_company_id')
    def _onchange_fiscal_position(self):
        """
        Sets the fiscal position based on operating company.
        """
        if not self.partner_id.property_account_position_id:
            self.fiscal_position_id = self.operating_company_id.fiscal_position_id
        if self.partner_id.state_id == self.operating_company_id.state_id:
            self.fiscal_position_id = False

    # @api.model
    # def fields_get(self, allfields=None, attributes=None):
    #     res = super().fields_get()
    #     if self.env.user.has_group(
    #         "account.group_account_invoice"
    #     ) or self.env.user.has_group("account.group_account_manager"):
    #         res["operating_company_id"]["readonly"] = False
    #     else:
    #         res["operating_company_id"]["readonly"] = True
    #     return res
