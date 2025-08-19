from odoo import api, models


class PaymentLinkWizard(models.TransientModel):
    _inherit = "payment.link.wizard"

    @api.depends(
        "description",
        "amount",
        "currency_id",
        "partner_id",
        "company_id",
        "payment_provider_selection",
    )
    def _compute_link(self):
        super()._compute_link()
        related_document = self.env[self.res_model].browse(self.res_id)
        if (
            related_document.operating_company_id
            and related_document.operating_company_id.payment_provider_ids
        ):
            provider_ids = related_document.operating_company_id.payment_provider_ids
            provider_ids_list = [provider.id for provider in provider_ids]
            provider_ids_data = "&provider_ids=" + str(provider_ids_list)
            self.link += provider_ids_data
            self._selection_payment_provider_selection()
        elif (
            related_document.operating_company_id
            and not related_document.operating_company_id.payment_provider_ids
        ):
            provider_ids_data = "&provider_ids=" + str([])
            self.link = ''

    def _get_payment_provider_available(self, **kwargs):
        res = super()._get_payment_provider_available(**kwargs)
        if kwargs.get("res_model") and kwargs.get("res_id"):
            related_document = self.env[kwargs.get("res_model")].browse(
                int(kwargs.get("res_id"))
            )
            if (
                related_document.operating_company_id
                and related_document.operating_company_id.payment_provider_ids
            ):
                provider_ids = (
                    related_document.operating_company_id.payment_provider_ids
                )
                res = provider_ids
            elif (
                related_document.operating_company_id
                and not related_document.operating_company_id.payment_provider_ids
            ):
                res = self.env["payment.provider"]

        return res
