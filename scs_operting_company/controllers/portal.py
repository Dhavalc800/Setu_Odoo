from odoo.addons.payment.controllers import portal
from odoo import http
from odoo.http import request
import ast


class PaymentPortalInherit(portal.PaymentPortal):
    @http.route(
        "/payment/pay",
        type="http",
        methods=["GET"],
        auth="public",
        website=True,
        sitemap=False,
    )
    def payment_pay(
        self,
        reference=None,
        amount=None,
        currency_id=None,
        partner_id=None,
        company_id=None,
        provider_id=None,
        provider_ids=None,
        access_token=None,
        **kwargs
    ):
        values = super().payment_pay(
            reference=reference,
            amount=amount,
            currency_id=currency_id,
            partner_id=partner_id,
            company_id=company_id,
            provider_id=provider_id,
            provider_ids=provider_ids,
            access_token=access_token,
            **kwargs
        )
        if not provider_id and provider_ids:
            provider_ids = ast.literal_eval(provider_ids)
            domain = [("id", "in", provider_ids)]
            fetched_provider_ids = request.env["payment.provider"].sudo().search(domain)
            if fetched_provider_ids:
                values.qcontext.update({"providers": fetched_provider_ids})
        return values
