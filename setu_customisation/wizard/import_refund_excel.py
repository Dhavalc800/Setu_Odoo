from odoo import models, fields
import base64
import xlrd

class ImportRefundExcel(models.TransientModel):
    _name = 'import.refund.excel'
    _description = 'Import Refund Excel'

    excel_file = fields.Binary(string="Excel File", required=True)
    file_name = fields.Char(string="File Name")

    def action_import_refunds(self):
        if not self.excel_file:
            return

        data = base64.b64decode(self.excel_file)
        workbook = xlrd.open_workbook(file_contents=data)
        sheet = workbook.sheet_by_index(0)

        for row in range(1, sheet.nrows):
            booking_id = sheet.cell_value(row, 0)
            print("\n\n\nBooking ID:", booking_id)
            if booking_id:
                sale_order = self.env['sale.order'].search([('name', '=', booking_id)], limit=1)
                if sale_order:
                    sale_order.is_refund = False
