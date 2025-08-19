from odoo import api, fields, models, exceptions, _
import json
import logging
import requests
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, AccessDenied, AccessError


class TataTeleConnector(models.Model):
    _name = 'tatatele.connector'
    _description = "Tata Tele Connector"

    def _get_config(self, config):
        token = config.access_token
        host = config.host
        return {"token": token, "host": host}

    def _build_headers(self, config, headers_add=None):
        auth_token = "{}".format(config["token"])
        headers = {
            "accept": "application/json",
            "Authorization": 'Bearer %s' % auth_token,
        }
        if headers_add:
            headers.update(headers_add)

        return headers

    def call(self, config, request_url, verb, headers=None, payload=None,
        # raise_errors=True,
    ):
        config = self._get_config(config)
        request_headers = self._build_headers(config, headers)
        request_data = payload and json.dumps(payload) or ""
        _logger.debug("\nRequest for %s %s:\n%s", request_url, verb, request_data)
        response = requests.request(
            verb,
            request_url,
            data=request_data,
            headers=request_headers,
        )

        # if response.status_code == 401:
            # raise AccessError(response.json().get('message'))
        print("response.status_code--------",response.status_code)
        # if response.status_code != 200:
        #     raise UserError(response.json().get('message'))
        return response
