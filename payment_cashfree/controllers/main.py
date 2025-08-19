# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug
import json
import requests
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CashfreeController(http.Controller):
    _return_url = '/return'

    @http.route(['/cashfree/return'], type='http', auth='public', csrf=False)
    def cashfree_return(self, **post):
        _logger.info("beginning DPN with post data:\n%s", pprint.pformat(post))

        if not post:
            pass
        else:
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
            'cashfree', post
            )
            provider_id = tx_sudo.provider_id
            order_details_post = self.get_order_status(provider_id, post)
            # Handle the notification data
            tx_sudo._handle_notification_data('cashfree', order_details_post)
        return request.redirect('/payment/status')


    def get_order_status(self, provider_id, post):
        order_id = post.get('order_id')
        if not order_id:
            raise ValidationError(_("No Order ID provided in the request."))

        url = provider_id.cashfree_get_form_action_url()
        url_with_order_id = f"{url}/{order_id}/payments"

        headers = {
            "accept": "application/json",
            "x-api-version": "2021-05-21",
            "x-client-id": provider_id.cashfree_app_id,
            "x-client-secret": provider_id.cashfree_secret_key,
        }

        try:
            response = requests.get(url_with_order_id, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            response_data = response.json()
            if not isinstance(response_data, list) or not response_data:
                raise ValidationError(_("Unexpected API response format. Data: %s") % pprint.pformat(response_data))
            return response_data[0]
        except requests.exceptions.HTTPError as e:
            _logger.exception(
                "HTTPError occurred while requesting %s with order ID: %s. Response: %s",
                url_with_order_id, order_id, e.response.text if e.response else "No response"
            )
            raise ValidationError(
                _("Cashfree: The communication with the API failed. Error: %s") % str(e)
            )

        except requests.exceptions.RequestException as e:
            _logger.exception(
                "RequestException occurred while requesting %s with order ID: %s. Exception: %s",
                url_with_order_id, order_id, str(e)
            )
            raise ValidationError(
                _("Cashfree: An error occurred while trying to communicate with the API. Please try again later.")
            )

        except ValueError as e:
            # Handles cases where the response is not valid JSON
            _logger.exception(
                "JSON decoding failed for order ID: %s at %s. Raw response: %s",
                order_id, url_with_order_id, response.text if response else "No response"
            )
            raise ValidationError(
                _("Cashfree: Unable to decode API response. Error: %s") % str(e)
            )
        except Exception as e:
            _logger.exception(
                "Unexpected error occurred while fetching order status for order ID: %s. Exception: %s",
                order_id, str(e)
            )
            raise ValidationError(
                _("Cashfree: An unexpected error occurred. Please contact support with the error details.")
            )
