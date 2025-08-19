from odoo import models, fields, api

class SaleOrderReportCustom(models.AbstractModel):
    _name = 'report.sale.action_report_saleorder'
    _inherit = 'report.report_saleorder.abstract'

    @api.model
    def _get_report_values(self, docids, data=None):
        sale_orders = self.env['sale.order'].browse(docids)
        for order in sale_orders:
            order.write({
                'pi_generated_by': self.env.user.id,
                'pi_generated_on': fields.Datetime.now(),
            })
        return super()._get_report_values(docids, data)