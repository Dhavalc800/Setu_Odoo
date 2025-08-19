from odoo import fields, models
import requests
import time


class PaymentLinkWizard(models.TransientModel):
    _inherit = 'payment.link.wizard'

    short_url_link = fields.Char(
        string="Payment Link")

    def _compute_link(self):
        rec = super(PaymentLinkWizard, self)._compute_link()
        for link in self:
            if link._context and link._context.get("active_model") == 'sale.order':
                order_id = link.env[link._context.get("active_model")].browse(
                    link._context.get("active_id"))
                if order_id and order_id.id:
                    print("\n\n\nlinkkkkkkkkkkkkkkkk",link)
                    if link.link:
                        timestamp_id = str(int(time.time()))
                        url_id = link.env['url.shortener'].create({
                            'short_code': timestamp_id,
                            'long_url': link.link
                        })
                        print("\n\n\nurl_id url_id url_id url_id",url_id.long_url)
                        short_url = url_id.generate_short_url()
                        order_id.write({
                            'link_generated_by': link.env.user,
                            'link_generated_on': fields.Datetime.now(),
                            'payment_link': short_url or link.link,
                        })
                    link.short_url_link = short_url or link.link