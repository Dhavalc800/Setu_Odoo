/** @odoo-module */

import checkoutForm from 'payment.checkout_form';
import manageForm from 'payment.manage_form';

const PaymentGenerateLink = {
    _prepareTransactionRouteParams: function (code, paymentOptionId, flow) {
        let res = this._super(...arguments);
        res['current_url'] =  window.location.href
        return res
    },
};

checkoutForm.include(PaymentGenerateLink);
manageForm.include(PaymentGenerateLink);
