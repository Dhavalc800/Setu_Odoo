from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date
import xlsxwriter
import tempfile
import base64
import os

class IncentiveSettlement(models.Model):
    _name = "incentive.settlement"
    _description = "Incentive Settlement"


    name = fields.Char(string="Name", copy=False, required=True)
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)
    state = fields.Selection([('draft', 'Draft'), ('review', 'Review'), ('settle', 'Settle'), ('cancel', 'Cancel')], string="Status", default='draft')
    incentive_lines = fields.One2many('incentive.settlement.line', 'incentive_settlement_id', string="Incentive Lines")
    refund_percentage = fields.Float(string="Refund Percentage")
    incentive_percentage = fields.Float(string="Incentive Percentage")

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                # Check if date_from is after date_to
                if record.date_from > record.date_to:
                    raise UserError(_("The 'Date From' must be prior to the 'Date To'!" + "\n" + "Please adjust the date range"))

    @api.constrains('refund_percentage', 'incentive_percentage')
    def _check_percentage(self):
        for record in self:
            if record.refund_percentage < 0 or record.refund_percentage > 100:
                raise UserError(_("The 'Refund Percentage' must be between 0 and 100!" + "\n" + "Please adjust the percentage"))
            if record.incentive_percentage < 0 or record.incentive_percentage > 100:
                raise UserError(_("The 'Incentive Percentage' must be between 0 and 100!" + "\n" + "Please adjust the percentage"))


    def get_account_payments(self, date_from, date_to):
        domain = [('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'posted'), ('settled', '=', False)]
        if self._context.get('adjust_settlement'):
            domain.append(('create_date', '>', date_to))
            # domain = ['|'] + domain + [('create_date', '>', date_to)]
        return self.env['account.payment'].search(domain)

    def calculate_sale_order_total_amount(self, reconciled_invoice_ids, date_to, date_from):
        sale_order_total_amount = {}
        refund_percentage = self.refund_percentage if self.refund_percentage > 0 else 0
        for invoice in reconciled_invoice_ids:
            invoice_paid_amount = 0
            refund_amount = 0
            payment_ids = []
            refund_payment_ids = []

            if invoice.invoice_payments_widget:
                content = invoice.invoice_payments_widget.get("content", [])
                for value in content:
                    account_payment_id = self.env['account.payment'].browse(value.get('account_payment_id'))
                    payment_date = value.get('date')
                    payment_amount = value.get("amount", 0)
                    if date_from <= payment_date <= date_to:
                        if account_payment_id.payment_type == 'inbound':
                            invoice_paid_amount += payment_amount
                            payment_ids.append(value.get('account_payment_id'))
                        elif account_payment_id.payment_type == 'outbound' and refund_percentage > 0:
                            refund_amount += (refund_percentage / 100) * payment_amount
                            refund_payment_ids.append(value.get('account_payment_id'))

            # Get sale orders linked to the invoice
            for sale_order in invoice.line_ids.mapped('sale_line_ids').filtered(
                    lambda x: x.order_id.state in ['done', 'sale'] and (not x.order_id.settled or self._context.get('adjust_settlement'))).mapped('order_id'):
                # Initialize if sale order is not already in the dictionary
                if sale_order not in sale_order_total_amount:
                    sale_order_total_amount[sale_order] = {'amount': 0, 'refund_amount': 0, 'payment_ids': [], 'refund_payment_ids': []}

                # Accumulate the amount and append the payment IDs
                sale_order_total_amount[sale_order]['amount'] += invoice_paid_amount
                sale_order_total_amount[sale_order]['refund_amount'] += refund_amount
                sale_order_total_amount[sale_order]['payment_ids'].extend(payment_ids)
                sale_order_total_amount[sale_order]['refund_payment_ids'].extend(refund_payment_ids)

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

    def get_previous_payments(self, sale_order, reconciled_invoice_ids, date_to):
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
        for invoice in sale_order.invoice_ids:
            if invoice.invoice_payments_widget:
                content = invoice.invoice_payments_widget.get("content", [])
                sum_of_content_amount = 0
                for value in content:
                    if value.get("date") and value.get("date") <= date_to:
                        sum_of_content_amount += value.get("amount", 0)
                if sum_of_content_amount - total_amount == 0:
                    remaining_payment_amount = 0
                else:
                    remaining_payment_amount = sum_of_content_amount - total_amount
        return remaining_payment_amount

    def get_incentive_lines(self):
        self.ensure_one()
        if not self._context.get('adjust_settlement'):
            self.incentive_lines.unlink()
        date_from = self.date_from
        date_to = self.date_to
        # Get account payments and reconciled invoice IDs
        account_payments = self.get_account_payments(date_from, date_to)
        reconciled_invoice_ids = account_payments.mapped('reconciled_invoice_ids')

        # Initialize user amounts dictionary
        user_collection_amounts = {}
        sale_order_total_amount = self.calculate_sale_order_total_amount(reconciled_invoice_ids, date_to, date_from)

        for sale_order, values in sale_order_total_amount.items():

            total_amount = values['amount']
            refund_amount = values['refund_amount']
            payment_ids = values['payment_ids']  # Payment IDs associated with the sale order
            refund_payment_ids = values['refund_payment_ids']
            sale_order_ids = [sale_order.id]
            tax_deducted = sale_order.order_line.get_tax_recieved_amount(sale_order, date_from, date_to, total_amount)
            cost_amount = self.get_cost_amount(sale_order, date_from, date_to, total_amount)

            # Deduce the margin from the total amount only if margin exceeds the paid amount
            if cost_amount > total_amount:
                # Get previous payment amount
                previous_payment_amt = self.get_previous_payments(sale_order, reconciled_invoice_ids, date_to)

                if previous_payment_amt > cost_amount:
                    amount_total = total_amount
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

            # Check if the sale order has multiple gamification data entries
            if len(sale_order.gamification_data_ids) > 1:
                for gamification_data in sale_order.gamification_data_ids:
                    user = gamification_data.salesperson_id
                    divided_amount = (gamification_data.percentage * amount_total) / 100
                    if user not in user_collection_amounts:
                        user_collection_amounts[user] = (0.0, refund_amount, [], [], refund_payment_ids)
                    current_amount, refund_amount, current_payment_ids, current_sale_order, refund_payment_ids = user_collection_amounts[user]
                    updated_payment_ids = list(set(current_payment_ids + payment_ids))
                    updated_sale_order_ids = list(set(current_sale_order + sale_order_ids))
                    user_collection_amounts[user] = (current_amount + divided_amount, refund_amount, updated_payment_ids, updated_sale_order_ids, refund_payment_ids)
                    print("refund_amount---if----------", refund_amount)

                if sale_order.pre_salesman_user_id:
                    pre_sales_user = sale_order.pre_salesman_user_id
                    pre_sales_amount = (sale_order.pre_sales_percentage * amount_total) / 100
                    if pre_sales_user not in user_collection_amounts:
                        user_collection_amounts[pre_sales_user] = (0.0, refund_amount, [], [], refund_payment_ids)

                    current_amount, refund_amount, current_payment_ids, current_sale_order, refund_payment_ids = user_collection_amounts[pre_sales_user]
                    updated_payment_ids = list(set(current_payment_ids + payment_ids))
                    updated_sale_order_ids = list(set(current_sale_order + sale_order_ids))
                    user_collection_amounts[pre_sales_user] = (current_amount + pre_sales_amount, refund_amount, updated_payment_ids, updated_sale_order_ids, refund_payment_ids)

            else:
                user = sale_order.user_id
                if user not in user_collection_amounts:
                    user_collection_amounts[user] = (0.0, refund_amount, [], [], refund_payment_ids)
                current_amount, refund_amount, current_payment_ids, current_sale_order, refund_payment_ids = user_collection_amounts[user]
                updated_payment_ids = list(set(current_payment_ids + payment_ids))
                updated_sale_order_ids = list(set(current_sale_order + sale_order_ids))
                user_collection_amounts[user] = (current_amount + amount_total, refund_amount, updated_payment_ids, updated_sale_order_ids, refund_payment_ids)
                print("refund_amount------else-------", refund_amount)

        # print("user_collection_amounts----------------", user_collection_amounts)
        return user_collection_amounts

    def create_incentive_lines(self):
        incentive_lines = self.get_incentive_lines()

        for user, (amount, refund_amount, payment_ids, sale_order_ids, refund_payment_ids) in incentive_lines.items():

            existing_user_line = self.incentive_lines.filtered(lambda l: l.sales_person_id.id == user.id)
            if existing_user_line:
                existing_user_line.collection_amount += amount
                existing_user_line.payment_ids = [(4, payment_id) for payment_id in payment_ids]
                existing_user_line.adjustment_amount += amount
            else:
                incentive_vals = {
                        'sales_person_id': user.id,
                        'collection_amount': amount,
                        'refund_amount': refund_amount,
                        'incentive_settlement_id': self.id,
                        'sale_order_ids': [(6, 0, sale_order_ids)],
                        'payment_ids': [(6, 0, payment_ids)],
                        'refund_payment_ids': [(6, 0, refund_payment_ids)],
                    }
                incentive_line = self.env['incentive.settlement.line'].create(incentive_vals)


    def action_review(self):
        for rec in self:
            if not rec.incentive_lines:
                raise UserError(_('Please add incentive lines'+ '\n' + 'You can add incentive lines of this duration by'
                                                                       ' clicking on "Get collection" button'))
            rec.state = 'review'

    def settle_entries(self):
        for rec in self:
            if rec.incentive_lines:
                for line in rec.incentive_lines:
                    for payment in line.payment_ids:
                        payment.settled = True
                    line.sale_order_ids.settled = True
            rec.state = 'settle'

    def action_cancel(self):
        for rec in self:
            if rec.incentive_lines:
                for line in rec.incentive_lines:
                    if line.sale_order_ids:
                        line.sale_order_ids.settled = False
                    if line.payment_ids:
                        line.payment_ids.settled = False
            rec.state = 'cancel'

    def generate_xlsx(self):
        attch_obj = self.env["ir.attachment"]
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
                   'Operating Company', 'Bank']

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
        for order in self.incentive_lines.mapped('sale_order_ids'):
            sheet.write(row, 0, order.name)
            sheet.write(row, 1, order.date_order.strftime('%Y-%m-%d') if order.date_order else '')
            sheet.write(row, 2, order.partner_id.name)
            sheet.write(row, 3, order.partner_id.mobile)

            product_lines = order.order_line.filtered(lambda l: not l.display_type and not l.is_downpayment)
            invoice_ids = order.invoice_ids
            payment_data = []

            for invoice in invoice_ids:
                if invoice.invoice_payments_widget:
                    content = invoice.invoice_payments_widget.get("content", [])
                    for value in content:
                        account_payment_id = self.env['account.payment'].browse(value.get('account_payment_id'))
                        if account_payment_id.payment_type == 'inbound':
                            if value.get("date") and value.get("date") <= self.date_to and value.get(
                                    "date") >= self.date_from:
                                payment_data.append({
                                    'payment_date': value.get('date').strftime('%Y-%m-%d') if value.get('date') else '',
                                    'ref': value.get('ref', ''),
                                    'amount': value.get('amount')
                                })

            max_rows = max(len(product_lines), len(payment_data))  # maximum rows needed

            # Loop over the maximum of product lines and payment data
            for i in range(max_rows):
                current_product_line = product_lines[i] if i < len(product_lines) else None
                current_payment = payment_data[i] if i < len(payment_data) else None

                # product line details, if available
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

                # Write common data (relevant for the first row of the order)
                if i == 0:
                    sheet.write(row, 10, order.payment_pending)
                    sheet.write(row, 11, order.margin)
                    sheet.write(row, 12, ','.join(order.gamification_data_ids.mapped('salesperson_id.name')))
                    sheet.write(row, 13, order.operating_company_id.name)
                    sheet.write(row, 14, order.bank_acc_id.display_name)
                else:
                    # Empty other fields for additional rows
                    sheet.write(row, 10, '')
                    sheet.write(row, 11, '')
                    sheet.write(row, 12, '')
                    sheet.write(row, 13, '')
                    sheet.write(row, 14, '')

                # Move to the next row
                row += 1

            # Add an empty row to separate orders
            row += 1

        # Close workbook and output
        workbook.close()
        buf = base64.encodebytes(open(file_path + '.xlsx', 'rb').read())
        try:
            if buf:
                os.remove(file_path + '.xlsx')
        except OSError:
            pass
        report_name = 'Incentive_Settlement_Report_%s.xlsx' % date.today().strftime('%Y-%m-%d')

        doc_id = attch_obj.create({
            'name': report_name,
            'datas': buf,
            'res_model': 'incentive.settlement',
            'res_id': self.id,
            'store_fname': 'Incentive Data Dump.xlsx'
        })
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/%s?download=true' % (doc_id.id),
            'target': 'current',
        }

    def check_and_adjust_settlement(self):
        self.create_incentive_lines()
        self.settle_entries()

    def set_to_draft(self):
        self.state = 'draft'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You can only delete draft records.'))
            return super(IncentiveSettlement, self).unlink()


class IncentiveSettlementLine(models.Model):
    _name = "incentive.settlement.line"
    _description = "Incentive Settlement Line"
    _rec_name = 'sales_person_id'

    incentive_settlement_id = fields.Many2one('incentive.settlement', string="Incentive Settlement", required=True)
    sales_person_id = fields.Many2one('res.users', string="Sales Person", required=True)
    collection_amount = fields.Float(string="Collection Amount", required=True)
    payment_ids = fields.Many2many('account.payment', 'incentive_payment_rel', 'incentive_id', 'payment_id',  string="Payments")
    sale_order_ids = fields.Many2many('sale.order', string="Sale Orders")
    adjustment_amount = fields.Float(string="Adjusted Amount")
    incentive_amount = fields.Float(string="Incentive Amount", compute="_compute_incentive_amount")
    refund_amount = fields.Float(string="Refund Amount")
    refund_payment_ids = fields.Many2many('account.payment', 'incentive_refund_payment_rel', 'incentive_id', 'refund_payment_id', string="Refund Payments")

    @api.depends('collection_amount', 'adjustment_amount')
    def _compute_incentive_amount(self):
        for record in self:
            record.incentive_amount = 0.0
            incentive_percentage = record.incentive_settlement_id.incentive_percentage
            if incentive_percentage > 0 and record.collection_amount:
                record.incentive_amount = (incentive_percentage / 100) * record.collection_amount
            record.incentive_amount -= record.refund_amount



class AccountPayment(models.Model):
    _inherit = "account.payment"

    settled = fields.Boolean(string="settled", copy=False)



class SaleOrder(models.Model):
    _inherit = "sale.order"

    settled = fields.Boolean(string="settled", copy=False)
