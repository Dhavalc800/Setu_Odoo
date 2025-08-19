from odoo import http
from odoo.http import request


class PaymentLinkExpire(http.Controller):

    @http.route('/payment/link/expired', type='http', auth='public', website=True, sitemap=False)
    def display_status(self, **kwargs):
        """ Display the payment status page.
            :param dict kwargs: Optional data. This parameter is not used here
            :return: The rendered status page
            :rtype: str
            """
        return request.render('sale_payment_generate_link.link_expire')
