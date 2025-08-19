/** @odoo-module */
/* global Stripe */

import checkoutForm from 'payment.checkout_form';
import manageForm from 'payment.manage_form';
import { StripeOptions } from '@payment_stripe/js/stripe_options';

const CashfreeMixin = {

    /**
     * Redirect the customer to Stripe hosted payment page.
     *
     * @override method from payment.payment_form_mixin
     * @private
     * @param {string} code - The code of the payment option
     * @param {number} paymentOptionId - The id of the payment option handling the transaction
     * @param {object} processingValues - The processing values of the transaction
     * @return {undefined}
     */
    _processRedirectPayment: function (code, paymentOptionId, processingValues) {
        if (code !== 'cashfree') {
            return this._super(...arguments);
        }
        location.replace(processingValues.api_url);
    },
};

checkoutForm.include(CashfreeMixin);
manageForm.include(CashfreeMixin);
