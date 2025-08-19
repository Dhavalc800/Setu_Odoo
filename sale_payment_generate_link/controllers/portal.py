from odoo.addons.payment.controllers import portal
from odoo import http
from odoo.http import request
import ast


class PaymentPortalInherit(portal.PaymentPortal):

    def _create_transaction(
        self, payment_option_id=None, reference_prefix=None, amount=None, currency_id=None, partner_id=None, flow=None,
        tokenization_requested=None, landing_route=None, is_validation=False,
        custom_create_values=None, **kwargs
    ):
        values = super()._create_transaction(
            payment_option_id=payment_option_id, reference_prefix=reference_prefix, amount=amount, currency_id=currency_id, partner_id=partner_id, flow=flow,
            tokenization_requested=tokenization_requested, landing_route=landing_route, is_validation=is_validation,
            custom_create_values=custom_create_values, **kwargs
        )
        values.write({'current_url': (kwargs.get('current_url'))})
        return values

    @http.route('/payment/confirmation', type='http', methods=['GET'], auth='public', website=True)
    def payment_confirm(self, tx_id, access_token, **kwargs):
        values = super().payment_confirm(tx_id=tx_id, access_token=access_token, **kwargs)
        transaction_ids = request.env['payment.transaction'].search(
            [('id', '=', tx_id), ('state', '=', 'done')])
        for transaction_id in transaction_ids:
            if transaction_id and transaction_id.current_url:
                current_transaction_url = request.env['url.shortener'].search(
                    [('long_url', '=', transaction_id.current_url)])
                if current_transaction_url:
                    current_transaction_url.unlink()
        return values
