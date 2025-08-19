from odoo import api, fields, models, _
from odoo.tools import float_round
from datetime import date
import xlsxwriter
import tempfile
import base64
import os


class SalePersonCollectionReport(models.TransientModel):
    _name = "sale.person.collection.report"
    _description = "Sale Person collection Report"
    _rec_name = 'user_id'


    user_id = fields.Many2one("res.users", "User", required=True)
    team_id = fields.Many2one("crm.team", "Sales Team")
    collection_amount = fields.Float("Target Amount")
    refund_percentage = fields.Integer("Refund(%)")
    refund_amount = fields.Float("Refund Amount")
    deduction_amount = fields.Float("Deduction Amount")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")


    def generate_report_response(self, res_ids, view_id, date_from, date_to, refund):
        header = f"Sale Person Target Report From {date_from or ''} To {date_to or ''}"
        return {
            "name": _(header),
            "type": "ir.actions.act_window",
            "view_mode": "tree",
            "res_model": "sale.person.collection.report",
            "view_id": view_id,
            "views": [(view_id, "tree")],
            "domain": [("id", "in", res_ids.ids)],
            "target": "main",
            "context": {'create': False}
        }

    def clear_existing_records(self):
        self.env.cr.execute("""DELETE FROM sale_person_collection_report""")

    def get_account_payments(self, date_from, date_to):
        return self.env['account.payment'].sudo().search(
            [('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'posted'),('payment_type','=','inbound')])

    def send_account_payments(self, date_from, date_to):
        return self.env['account.payment'].sudo().search(
            [('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'posted'),('payment_type','=','outbound')])

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

    def get_cost_amount(self, sale_order, date_from, date_to, total_amount):
        cost_amount = 0
        for order_line in sale_order.order_line:
            if order_line.purchase_price > 0:
                cost_amount += order_line.purchase_price
            if order_line.agent_ids:
                cost_amount += sum(order_line.mapped("agent_ids.amount"))
        tax_amount = sale_order.order_line.get_tax_recieved_amount(sale_order, date_from, date_to, total_amount)
        cost_amount += tax_amount.get('during_period') if tax_amount else 0
        return cost_amount

    def get_previous_payments(self, sale_order, reconciled_invoice_ids, date_to, total_amount):
        invoice_paid_amount = 0
        for invoice in sale_order.invoice_ids - reconciled_invoice_ids:
            if invoice.invoice_payments_widget:
                content = invoice.invoice_payments_widget.get("content", [])
                for value in content:
                    if value.get("date") and value.get("date") <= date_to:
                        invoice_paid_amount += value.get("amount", 0)
        return invoice_paid_amount

    def get_remaining_payment_amount(self, sale_order, date_to, total_amount):
        remaining_payment_amount = 0
        sum_of_content_amount = 0
        for invoice in sale_order.invoice_ids:
            if invoice.invoice_payments_widget:
                content = invoice.invoice_payments_widget.get("content", [])
                # if len(content) == 1:
                for value in content:
                    if value.get("date") and value.get("date") <= date_to:
                        sum_of_content_amount += value.get("amount", 0)
                if sum_of_content_amount - total_amount == 0:
                    remaining_payment_amount = 0
                else:
                    remaining_payment_amount = sum_of_content_amount - total_amount
        return remaining_payment_amount

    # def create_collection_records(self, user_collection_amounts,, date_from, date_to, refund):
    #     vals_list = []
    #     for user, collection_amount in user_collection_amounts.items():
    #         print("user, collection_amount", user, collection_amount, refund)
    #         remaining_amount = collection_amount - (collection_amount * refund / 100)
    #         refund_amount = collection_amount * (refund / 100)
    #         vals = {
    #             'user_id': user.id,
    #             'collection_amount': collection_amount,
    #             'refund_percentage': refund,
    #             'refund_amount': refund_amount,
    #             'remaining_amount': remaining_amount,
    #             'date_from': date_from,
    #             'date_to': date_to,
    #         }
    #         vals_list.append(vals)
    #     return self.create(vals_list)

    def create_collection_records(self, user_collection_amounts, cr_user_collection_amounts, date_from, date_to, refund):
        vals_dict = {}
        for user, collection_amount in user_collection_amounts.items():
            team = self.env['crm.team'].search([('member_ids', 'in', [user.id])])
            vals_dict[user] = {
                'user_id': user.id,
                'team_id': team.id,
                'collection_amount': collection_amount,
                'date_from': date_from,
                'date_to': date_to,
                'refund_percentage': 0,
                'refund_amount': 0,
            }

        for user, cr_collection_amount in cr_user_collection_amounts.items():
            refund_amount = cr_collection_amount * (refund / 100)
            deduction_amount = cr_collection_amount + refund_amount
            if user in vals_dict:
                vals_dict[user].update({
                    'refund_percentage': refund,
                    'refund_amount': cr_collection_amount,
                    'deduction_amount': deduction_amount,
                })

                vals_dict[user]['collection_amount'] -= deduction_amount

        vals_list = list(vals_dict.values())
        return self.create(vals_list)

    def sale_person_collection_report(self, date_from, date_to, refund):
        view_id = self.env.ref("scs_sales_person_report.sale_person_collection_report_tree_view").id
        self.clear_existing_records()
        account_payments = self.get_account_payments(date_from, date_to)
        sending_account_payments = self.send_account_payments(date_from, date_to)
        reconciled_invoice_ids = account_payments.mapped('reconciled_invoice_ids')
        cr_reconciled_invoice_ids = sending_account_payments.mapped('reconciled_invoice_ids')

        user_collection_amounts = {}
        cr_user_collection_amounts = {}

        sale_order_total_amount = self.calculate_sale_order_total_amount(reconciled_invoice_ids, date_to, date_from)
        for sale_order, total_amount in sale_order_total_amount.items():
            tax_deducted = sale_order.order_line.get_tax_recieved_amount(sale_order,date_from, date_to, total_amount)
            cost_amount = self.get_cost_amount(sale_order, date_from, date_to, total_amount)
            if cost_amount > total_amount:
                previous_payment_amt = self.get_previous_payments(sale_order, reconciled_invoice_ids, date_to, total_amount=0.0)
                if previous_payment_amt > cost_amount:
                    amount_total = total_amount - tax_deducted.get('during_period') if tax_deducted else 0
                else:
                    total_amount = previous_payment_amt + total_amount
                    if total_amount <= cost_amount:
                        continue
                    amount_total = total_amount - cost_amount
            else:
                remaining_amt = self.get_remaining_payment_amount(sale_order, date_to, total_amount)
                if remaining_amt > cost_amount:
                    amount_total = total_amount - tax_deducted.get('during_period') if tax_deducted else 0
                else:
                    amount_total = total_amount - cost_amount
            if len(sale_order.gamification_data_ids) >= 1:
                for gamification_data in sale_order.gamification_data_ids:
                    user = gamification_data.salesperson_id
                    divided_amount = (gamification_data.percentage * amount_total) / 100
                    if user not in user_collection_amounts:
                        user_collection_amounts[user] = 0.0
                    user_collection_amounts[user] += divided_amount

                if sale_order.pre_salesman_user_id:
                    pre_sales_user = sale_order.pre_salesman_user_id
                    pre_sales_amount = (sale_order.pre_sales_percentage * amount_total) / 100

                    if pre_sales_user not in user_collection_amounts:
                        user_collection_amounts[pre_sales_user] = 0.0
                    user_collection_amounts[pre_sales_user] += pre_sales_amount
            else:
                user = sale_order.user_id
                if user not in user_collection_amounts:
                    user_collection_amounts[user] = 0.0
                user_collection_amounts[user] += amount_total


        cr_sale_order_total_amount = self.calculate_sale_order_total_amount(cr_reconciled_invoice_ids, date_to, date_from)

        for sale_order, total_amount in cr_sale_order_total_amount.items():
            tax_deducted = sale_order.order_line.get_tax_recieved_amount(sale_order,date_from, date_to, total_amount)
            cost_amount = self.get_cost_amount(sale_order, date_from, date_to, total_amount)
            if cost_amount > total_amount:
                previous_payment_amt = self.get_previous_payments(sale_order, reconciled_invoice_ids, date_to, total_amount=0.0)
                if previous_payment_amt > cost_amount:
                    amount_total = total_amount - tax_deducted.get('during_period') if tax_deducted else 0
                else:
                    total_amount = previous_payment_amt + total_amount
                    if total_amount <= cost_amount:
                        continue
                    amount_total = total_amount - cost_amount
            else:
                remaining_amt = self.get_remaining_payment_amount(sale_order, date_to, total_amount)
                if remaining_amt > cost_amount:
                    amount_total = total_amount - tax_deducted.get('during_period') if tax_deducted else 0
                else:
                    amount_total = total_amount - cost_amount
            if len(sale_order.gamification_data_ids) >= 1:
                for gamification_data in sale_order.gamification_data_ids:
                    user = gamification_data.salesperson_id
                    divided_amount = (gamification_data.percentage * amount_total) / 100
                    if user not in cr_user_collection_amounts:
                        cr_user_collection_amounts[user] = 0.0
                    cr_user_collection_amounts[user] += divided_amount
            else:
                user = sale_order.user_id
                if user not in cr_user_collection_amounts:
                    cr_user_collection_amounts[user] = 0.0
                cr_user_collection_amounts[user] += amount_total

        res_ids = self.create_collection_records(user_collection_amounts, cr_user_collection_amounts, date_from, date_to, refund)
        return self.generate_report_response(res_ids, view_id, date_from, date_to, refund)


    def generate_xlsx(self):
        attch_obj = self.env["ir.attachment"]
        for record in self:
            file_path = tempfile.NamedTemporaryFile().name
            workbook = xlsxwriter.Workbook(file_path + '.xlsx')
            sheet = workbook.add_worksheet('Incentive Report')

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

            headers = ['Order Reference', 'Creation Date', 'Customer', 'Customer/Mobile', 'Order Lines/Product', 'Total', 'Order Lines/Cost',
                       'Payment Date', 'Transaction ID', 'Payment Received', 'Payment Pending', 'Margin', 'Gamification Data/Salespersons',
                       'Sale Team','Operating Company', 'Bank']

            # headers to the first row
            for col, header in enumerate(headers):
                sheet.write(0, col, header, header_format)

            # column widths for better visibility of longer headers
            column_widths = [12, 13, 25, 18, 30, 10, 15, 15, 30, 18, 18, 10, 25, 30, 25]
            for col, width in enumerate(column_widths):
                sheet.set_column(col, col, width)

            # row height for the header row
            sheet.set_row(0, 30)
            row = 1

            account_payments = self.get_account_payments(record.date_from, record.date_to)
            reconciled_invoice_ids = account_payments.mapped('reconciled_invoice_ids')
            sale_order_total_amount = self.calculate_sale_order_total_amount(reconciled_invoice_ids, record.date_to, record.date_from)

            for sale_order, total_amount in sale_order_total_amount.items():
                sheet.write(row, 0, sale_order.name)
                sheet.write(row, 1, sale_order.date_order.strftime('%Y-%m-%d') if sale_order.date_order else '')
                sheet.write(row, 2, sale_order.partner_id.name)
                sheet.write(row, 3, sale_order.partner_id.mobile)

                product_lines = sale_order.order_line.filtered(lambda l: not l.display_type)
                invoice_ids = sale_order.invoice_ids
                payment_data = []

                for invoice in invoice_ids:
                    if invoice.invoice_payments_widget:
                        content = invoice.invoice_payments_widget.get("content", [])
                        for value in content:
                            account_payment_id = self.env['account.payment'].browse(value.get('account_payment_id'))
                            if account_payment_id.payment_type == 'inbound':
                                if value.get("date") and value.get("date") <= record.date_to and value.get(
                                        "date") >= record.date_from:
                                    payment_data.append({
                                        'payment_date': value.get('date').strftime('%Y-%m-%d') if value.get('date') else '',
                                        'ref': value.get('ref', ''),
                                        'amount': value.get('amount')
                                    })
                max_rows = max(len(product_lines), len(payment_data))

                # Loop over the maximum of product lines and payment data
                for i in range(max_rows):
                    current_product_line = product_lines[i] if i < len(product_lines) else None
                    current_payment = payment_data[i] if i < len(payment_data) else None

                    if current_product_line:
                        sheet.write(row, 4, current_product_line.product_id.name)
                        sheet.write(row, 5, current_product_line.price_total)
                        sheet.write(row, 6, current_product_line.purchase_price)
                    else:
                        sheet.write(row, 4, '')
                        sheet.write(row, 5, '')
                        sheet.write(row, 6, '')

                    # payment details, if available
                    if current_payment:
                        sheet.write(row, 7, current_payment['payment_date'])
                        sheet.write(row, 8, current_payment['ref'])
                        sheet.write(row, 9, current_payment['amount'])
                    else:
                        sheet.write(row, 7, '')
                        sheet.write(row, 8, '')
                        sheet.write(row, 9, '')


                    if i == 0:
                        sheet.write(row, 10, sale_order.payment_pending)
                        sheet.write(row, 11, sale_order.margin)
                        sheet.write(row, 12, ','.join(sale_order.gamification_data_ids.mapped('salesperson_id.name')))
                        sheet.write(row, 13, sale_order.team_id.name)
                        sheet.write(row, 14, sale_order.operating_company_id.name)
                        sheet.write(row, 15, sale_order.bank_acc_id.display_name)
                    else:
                        # Empty other fields for additional rows
                        sheet.write(row, 10, '')
                        sheet.write(row, 11, '')
                        sheet.write(row, 12, '')
                        sheet.write(row, 13, '')
                        sheet.write(row, 14, '')
                        sheet.write(row, 15, '')

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
            report_name = 'Sale_person_collection_report_%s.xlsx' % date.today().strftime('%Y-%m-%d')

            doc_id = attch_obj.create({
                'name': report_name,
                'datas': buf,
                'res_model': 'sale.person.collection.report',
                'res_id': record.id,
                'store_fname': 'Sale Person Collection Dump.xlsx'
            })

            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/%s?download=true' % (doc_id.id),
                'target': 'current',
            }

