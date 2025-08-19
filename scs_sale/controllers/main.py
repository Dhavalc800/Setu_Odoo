import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import html_escape


class BookingPaymentLink(http.Controller):

    @http.route('/booking-payment/<int:short_code>', type='http', auth='public', methods=['GET'], csrf=False)
    def short_payment_link(self, short_code, **kw):
        if short_code:
            link = request.env['url.shortener'].sudo().search(
                [('short_code', '=', short_code)])

            if link and link.long_url:
                return request.redirect(link.long_url)
            else:
                return request.redirect('/payment/link/expired')
        else:
            return request.redirect('/web')
