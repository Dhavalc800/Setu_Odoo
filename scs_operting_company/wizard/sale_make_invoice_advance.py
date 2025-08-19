from odoo import fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _default_operating_compnay(self):
        if self._context.get("active_model") == "sale.order":
            sale_id = self.env[self._context.get("active_model")].browse(
                self._context.get("active_id")
            )
            return sale_id.operating_company_id.id

    operating_company_id = fields.Many2one(
        comodel_name="operating.company",
        default=_default_operating_compnay,
        required=1,
        copy=False,
    )

    def _create_invoices(self, sale_orders):
        if self.sale_order_ids and self.operating_company_id:
            self.sale_order_ids.write(
                {"operating_company_id": self.operating_company_id.id}
            )
        invoice = super()._create_invoices(sale_orders)
        return invoice
