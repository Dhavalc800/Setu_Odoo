# -*- coding: utf-8 -*-

import hashlib
import hmac
import base64

from werkzeug import urls

from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class PaymentProviderCashfree(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('cashfree', 'Cashfree')], ondelete={"cashfree": "set default"})
    cashfree_app_id = fields.Char(string='App id', required_if_provider='cashfree', groups='base.group_user')
    cashfree_secret_key = fields.Char(string='Secret Key', required_if_provider='cashfree', groups='base.group_user')

    def _get_cashfree_urls(self, environment):
        """ Cashfree URLs"""
        if environment == 'enabled':
            return {'cashfree_form_url': 'https://api.cashfree.com/pg/orders'}
        else:
            return {'cashfree_form_url': 'https://sandbox.cashfree.com/pg/orders'}


    def cashfree_get_form_action_url(self):
        self.ensure_one()
        return self._get_cashfree_urls(self.state)['cashfree_form_url']