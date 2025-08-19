from odoo import _, fields, models,api
from odoo.exceptions import UserError, ValidationError
import logging
import requests
import json
import base64
from odoo.addons.payment_cashfree.controllers.main import CashfreeController
_logger = logging.getLogger(__name__)
try:
    # For Python 3.0 and later
    from urllib.parse import urljoin
except ImportError:
    # For Python 2's urllib2
    from urlparse import urljoin
from odoo.addons.phone_validation.tools.phone_validation import phone_sanitize_numbers


class TxCashfree(models.Model):
    _inherit = "payment.transaction"

    # def _get_specific_processing_values(self, processing_values):
    #     suoer()._process_notification_data

    def _get_specific_rendering_values(self,processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        self.partner_phone = self.partner_id.mobile
        if self.provider_code != 'cashfree':
            return res
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        cashfree_tx_processing_values = dict(processing_values)
        appID = self.provider_id.cashfree_app_id
        secret_key = self.provider_id.cashfree_secret_key
        headers = {
            "accept": "application/json",
            "x-client-id": appID,
            "x-client-secret": secret_key,
            "x-api-version": "2021-05-21",
            "content-type": "application/json"
        }

        customer_Id = cashfree_tx_processing_values.get("partner_id")
        order_id = cashfree_tx_processing_values.get("reference")
        customerEmail = self.partner_email
        phone = self.partner_id.mobile
        error_message = _("The phone number is missing.")
        if phone:
            # sanitize partner phone
            country_code = self.partner_country_id.code
            country_phone_code = self.partner_country_id.phone_code
            phone_info = phone_sanitize_numbers([phone], country_code, country_phone_code)
            phone = phone_info[phone]['sanitized']
            error_message = phone_info[phone]['msg']
        if not phone:
            raise ValidationError("cashfree: " + error_message)
        url = self.provider_id.cashfree_get_form_action_url()
        print ("\n self.currency_id.name",self.currency_id.name)
        return_url = urljoin(
                base_url,
                f'/cashfree/return?order_id={"{order_id}"}'
            )
        data_dict = json.dumps({
            "customer_details": {
                "customer_id": str(customer_Id),
                "customer_email": customerEmail or '',
                "customer_phone": phone
            },
            "order_meta": {
                "return_url": return_url
                }, 
            "order_amount": cashfree_tx_processing_values.get("amount"),
            "order_currency": self.currency_id.name,
        })
        response = requests.request("POST", url, headers=headers, data=data_dict)
        response_json = response.json()
        if response_json.get("type") == 'invalid_request_error':
            error_msg = (_('%s') % (response_json.get("message")))
            raise ValidationError(error_msg)
        else:
            cashfree_tx_processing_values.update({
                "api_url": "%s" % response_json.get("payment_link"),
                "order_currency": "%s" % self.currency_id.name,
                "orderId": "%s" % response_json.get("order_id"), 
                # "app_id" : 
                # "": 

            })
            processing_values.update({
                "api_url": "%s" % response_json.get("payment_link"),
            })
            self.write({'reference': response_json.get("order_id")})
        _logger.info(cashfree_tx_processing_values)

        return cashfree_tx_processing_values
    
    @api.model
    def _get_tx_from_notification_data(self, provider, data):
        tx = super()._get_tx_from_notification_data(provider, data)
        if provider != 'cashfree':
            return tx
        reference = data.get("order_id")
        if not reference:
            cashfree_error = data.get("message")
            _logger.error(
                "Cashfree: invalid reply received from Cashfree API, "
                "looks like the transaction failed. (error: %s)",
                cashfree_error or "n/a")
            error_msg = _(
                "We're sorry to report that the transaction has failed.")
            if cashfree_error:
                error_msg += " " + (_(
                    "Cashfree following info about the problem: %s") %
                    cashfree_error)
            error_msg += " " + _(
                "problem can be solved by double-checking your "
                "credit card details, or contacting your bank?")
            raise ValidationError(error_msg)
        tx = self.search([("reference", "=", reference)])
        if not tx:
            error_msg = (_(
                "Cashfree: no order found for reference %s") % reference)
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        elif len(tx) > 1:
            error_msg = (_(
                "Cashfree: %s orders found for reference %s") % (
                    len(tx), reference))
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return tx[0]

    def _process_notification_data(self, data):
        super()._process_notification_data(data)
        if self.provider_code != 'cashfree':
            return
        provider_reference = data.get("order_id")
        if provider_reference:

            self.write({
                "provider_reference": provider_reference,
            })
            if data.get('payment_status') == 'SUCCESS':
                self._set_done()
            elif data.get('payment_status') == 'FAILED':
                self._set_canceled()
            elif data.get('payment_status') == 'PENDING':
                self._set_pending()
            # elif data.get('payment_status') == 'USER_DROPPED':
            #     self._set_pending()

            self._execute_callback()
            if self.token_id:
                self.token_id.verified = True
            return True
        else:
            error = data.get("payment_status")
            _logger.info(error)
            self.write({
                "state_message": error,
            })
            self._set_error(
                    _("An error occurred during the processing of your payment. Please try again.")
                )
            return False
