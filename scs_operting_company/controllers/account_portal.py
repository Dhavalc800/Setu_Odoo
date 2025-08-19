from odoo.addons.account_payment.controllers import portal


class PortalAccountInherit(portal.PortalAccount):
    def _invoice_get_page_view_values(self, invoice, access_token, **kwargs):
        values = super()._invoice_get_page_view_values(invoice, access_token, **kwargs)
        if (
            invoice.operating_company_id
            and invoice.operating_company_id.payment_provider_ids
        ):
            values.update(
                {"providers": invoice.operating_company_id.payment_provider_ids}
            )
        elif invoice.operating_company_id and not invoice.operating_company_id.payment_provider_ids:
            values.update(
                {"providers": invoice.operating_company_id.payment_provider_ids}
            )

        return values
