from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date
import xlsxwriter
import tempfile
import base64
import os


class AccountTallyReport(models.TransientModel):
    _name = "account.tally.report.wizard"
    _description = "Account Tally Report Wizard"

    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        records = self.filtered(lambda rec: rec.date_from and rec.date_to and rec.date_from > rec.date_to)
        if records:
            raise UserError("The 'Date From' cannot be after the 'Date To'!")

    def get_account_payments(self, date_from, date_to):
        return self.env['account.payment'].sudo().search(
            [('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'posted'),('payment_type','=','inbound')])

    def calculate_sale_order_total_amount(self, reconciled_invoice_ids, date_to, date_from):
        sale_order_total_amount = {}
        for invoice in reconciled_invoice_ids:
            invoice_paid_amount = 0
            if invoice.invoice_payments_widget:
                content = invoice.invoice_payments_widget.get("content", [])
                invoice_paid_amount += sum(value.get("amount", 0) for value in content if value.get('date') <= date_to and value.get('date') >= date_from)
            for sale_order in invoice.line_ids.mapped('sale_line_ids').filtered(lambda x: x.order_id.state in ['done', 'sale']).mapped('order_id'):
                if sale_order not in sale_order_total_amount:
                    sale_order_total_amount[sale_order] = 0
                sale_order_total_amount[sale_order] += invoice_paid_amount
        return sale_order_total_amount


    def generate_xlsx(self):
        attch_obj = self.env["ir.attachment"]
        for record in self:
            file_path = tempfile.NamedTemporaryFile().name
            workbook = xlsxwriter.Workbook(file_path + '.xlsx')
            sheet = workbook.add_worksheet('Account Tally Report')

            # header format
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#4CAF50',
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
                'text_wrap': True,
                'font_size': 12,
            })

            # Freeze the first row
            sheet.freeze_panes(1, 0)

            headers = [
            'PAYMENT RECEIVE DATE',
            'CRM UPDATE DATE',
            'Company Name',
            'Booking id',
            'Total Received Amount',
            'Bdm Name',
            'Bank Name',
            'Recipient Bank',
            'PAYMENT REF',
            'SERVICE',
            'PAYMENT MODE',
            'TDS AMOUNT',
            'Customer Name' ,
            'GST NUMBER',
            'PAN CARD']

            # headers to the first row
            for col, header in enumerate(headers):
                sheet.write(0, col, header, header_format)

            # column widths for better visibility of longer headers
            column_widths = [30, 25, 45, 15, 20, 25, 25, 25, 35, 45, 15, 18 ,45, 18, 18]
            # column_widths = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 13, 14]
            for col, width in enumerate(column_widths):
                sheet.set_column(col, col, width)

            # row height for the header row
            sheet.set_row(0, 30)
            row = 1

            account_payments = self.get_account_payments(record.date_from, record.date_to)
            reconciled_invoice_ids = account_payments.mapped('reconciled_invoice_ids')
            sale_order_total_amount = self.calculate_sale_order_total_amount(reconciled_invoice_ids, record.date_to, record.date_from)

            for sale_order, total_amount in sale_order_total_amount.items():
                sheet.write(row, 1, sale_order.lock_date.strftime('%Y-%m-%d') if sale_order.lock_date else '')
                sheet.write(row, 2, sale_order.operating_company_id.name)
                sheet.write(row, 3, sale_order.name)
                sheet.write(row, 5, sale_order.user_id.name)
                sheet.write(row, 6, sale_order.bank_acc_id.display_name)
                sheet.write(row, 12, sale_order.partner_id.name)
                sheet.write(row, 13, sale_order.partner_id.vat or '')
                sheet.write(row, 14, sale_order.partner_id.l10n_in_pan or '')

                product_lines = sale_order.order_line.filtered(lambda l: not l.display_type)
                invoice_ids = sale_order.invoice_ids
                payment_data = []

                for invoice in invoice_ids.filtered(lambda inv: inv.invoice_payments_widget):
                    content = invoice.invoice_payments_widget.get("content", [])
                    for value in content:
                        payment_id = value.get('account_payment_id')
                        payment_date = value.get("date")
                        if payment_id and payment_date and record.date_from <= payment_date <= record.date_to:
                            account_payment = self.env['account.payment'].browse(payment_id)
                            if account_payment.payment_type == 'inbound':
                                payment_data.append({
                                    'payment_date': payment_date.strftime('%Y-%m-%d'),
                                    'ref': value.get('ref', ''),
                                    'amount': value.get('amount'),
                                    'mode': value.get('payment_method_name'),
                                })
                    # tds_lines = invoice.line_ids.filtered(
                    #     lambda line: any(
                    #         keyword in (line.account_id.name or '').upper() 
                    #         for keyword in ['TDS DEDUCTED']
                    #     )
                    # )

                    tds_lines = invoice.line_ids.filtered(
                        lambda line: 'TDS' in (line.account_id.name or '').upper()
                    )
                    # tds_lines = invoice.line_ids.filtered(lambda line: line.account_id.name and 'TDS Deducted' in line.account_id.name)

                    tds_amount = sum(tds_lines.mapped('debit'))

                max_rows = max(len(product_lines), len(payment_data))
                for i in range(max_rows):
                    current_product_line = product_lines[i] if i < len(product_lines) else None
                    current_payment = payment_data[i] if i < len(payment_data) else None

                    if current_product_line:
                        sheet.write(row, 9, current_product_line.product_id.name)

                    if current_payment:
                        sheet.write(row, 0, current_payment['payment_date'])
                        sheet.write(row, 7, invoice.partner_bank_id.display_name)
                        sheet.write(row, 8, invoice.payment_reference)
                        sheet.write(row, 10, current_payment['mode'])
                        sheet.write(row, 11, tds_amount)
                        sheet.write(row, 4, current_payment['amount'])
                    row += 1
                row += 1


            # Close workbook and output
            workbook.close()
            buf = base64.encodebytes(open(file_path + '.xlsx', 'rb').read())
            try:
                if buf:
                    os.remove(file_path + '.xlsx')
            except OSError:
                pass
            report_name = 'account_tally_report%s.xlsx' % date.today().strftime('%Y-%m-%d')

            doc_id = attch_obj.create({
                'name': report_name,
                'datas': buf,
                'res_model': 'account.tally.report.wizard',
                'res_id': record.id,
                'store_fname': 'Account Tally Report Dump.xlsx'
            })

            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/%s?download=true' % (doc_id.id),
                'target': 'current',
            }
