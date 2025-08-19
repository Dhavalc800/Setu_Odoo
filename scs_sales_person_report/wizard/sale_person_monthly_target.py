from odoo import api, fields, models, _
from odoo.tools import float_round



class SalePersonMonthlyTarget(models.TransientModel):
    _name = "sale.person.monthly.target"
    _description = "Sale Person Target Line"
    _rec_name = 'user_id'
    _order = 'percentage desc'

    user_id = fields.Many2one("res.users", "User", required=True)
    employee_id = fields.Many2one(related='user_id.employee_id', string="Employee")
    amount = fields.Float("Target Amount")
    sale_person_target_id = fields.Many2one("sale.person.target", "Sale Person Target")
    collection_amount = fields.Float(string="Collection Amount")
    pending_amount = fields.Float(compute="_compute_pending_amount", string="Pending Amount")
    percentage = fields.Float(string="Percentage")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")

    @api.depends('amount', 'collection_amount')
    def _compute_pending_amount(self):
        for rec in self:
            rec.pending_amount = rec.amount - rec.collection_amount

    def get_percentage(self, collection_amount, amount):
        percentage = 0
        if collection_amount > 0 and amount > 0:
            percentage = float_round((collection_amount / amount) * 100, precision_digits=0, rounding_method='UP') / 100
        return percentage

    def clear_existing_records(self):
        self.env.cr.execute("""DELETE FROM sale_person_monthly_target""")

    def get_current_month_target(self, date_from, date_to):
        return self.env['sale.person.target'].search(
            [('start_date', '=', date_from), ('end_date', '=', date_to), ('state', '=', 'confirm')],
            limit=1
        )

    def get_account_payments(self, date_from, date_to):
        return self.env['account.payment'].search(
            [('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'posted')])

    def get_cost_amount(self, sale_order, date_from, date_to, total_amount):
        cost_amount = 0
        for order_line in sale_order.order_line.filtered(lambda l: not l.display_type and not l.is_downpayment):
            if order_line.purchase_price > 0:
                cost_amount += order_line.purchase_price
            if order_line.agent_ids:
                cost_amount += sum(order_line.mapped("agent_ids.amount"))
        tax_amount = sale_order.order_line.get_tax_recieved_amount(sale_order, date_from, date_to, total_amount)
        cost_amount += tax_amount.get('during_period') if tax_amount else 0
        return cost_amount

    # def get_previous_payments(self, sale_order, reconciled_invoice_ids, date_to):
    #     invoice_paid_amount = 0
    #     for invoice in sale_order.invoice_ids:
    #         print("invoice---------------------", invoice)
    #         if invoice.payment_state == "partial":
    #             print("partial-------if---------------------")
    #             if invoice.invoice_payments_widget:
    #                 content = invoice.invoice_payments_widget.get("content", [])
    #                 # if len(content) > 1:
    #                 for value in content:
    #                     print("value---------", value)
    #                     if value.get("date") and value.get("date") <= date_to:
    #                         invoice_paid_amount += value.get("amount", 0)
    #                 # else:
    #                 #     for value in content:
    #                 #         if value.get("date") and value.get("date") <= date_to:
    #                 #             invoice_paid_amount += value.get("amount", 0)
    #         else:
    #             print("partial-------else---------------------")
    #             if len(sale_order.invoice_ids) > 1:
    #                 print("len(sale_order.invoice_ids) > 1-------if---------------------")
    #                 for invoice in sale_order.invoice_ids - reconciled_invoice_ids:
    #                     if invoice.invoice_payments_widget:
    #                         content = invoice.invoice_payments_widget.get("content", [])
    #                         for value in content:
    #                             if value.get("date") and value.get("date") <= date_to:
    #                                 invoice_paid_amount += value.get("amount", 0)
    #             else:
    #                 print("len(sale_order.invoice_ids) > 1-------else---------------------")
    #                 for invoice in sale_order.invoice_ids:
    #                     if invoice.invoice_payments_widget:
    #                         content = invoice.invoice_payments_widget.get("content", [])
    #                         for value in content:
    #                             if value.get("date") and value.get("date") <= date_to:
    #                                 invoice_paid_amount += value.get("amount", 0)
    #     print("invoice_paid_amount------------------", invoice_paid_amount)
    #     return invoice_paid_amount

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
        for invoice in sale_order.invoice_ids:
            if invoice.invoice_payments_widget:
                content = invoice.invoice_payments_widget.get("content", [])
                sum_of_content_amount = 0
                # if len(content) == 1:
                for value in content:
                    if value.get("date") and value.get("date") <= date_to:
                        sum_of_content_amount += value.get("amount", 0)
                if sum_of_content_amount - total_amount == 0:
                    remaining_payment_amount = 0
                else:
                    remaining_payment_amount = sum_of_content_amount - total_amount
        return remaining_payment_amount

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

    def no_target_found_response(self, view_id):
        return {
            "name": _("No target found for the given period."),
            "type": "ir.actions.act_window",
            "view_mode": "tree",
            "res_model": "sale.person.monthly.target",
            "view_id": view_id,
            "views": [(view_id, "tree")],
            "target": "main",
            "context": {'create': False}
        }

    def create_target_lines(self, current_month_target, target_lines, user_amounts, date_from, date_to):
        vals_list = []
        for target_line in target_lines:
            collection_amount = user_amounts.get(target_line.user_id, 0.0)
            vals = {
                'user_id': target_line.user_id.id,
                'amount': target_line.amount,
                'collection_amount': collection_amount,
                'sale_person_target_id': current_month_target.id,
                'date_from': date_from,
                'date_to': date_to,
                'percentage': self.get_percentage(collection_amount, target_line.amount)
            }
            vals_list.append(vals)
        return self.create(vals_list)

    def generate_report_response(self, res_ids, view_id, date_from, date_to):
        header = f"Sale Person Target Report From {date_from or ''} To {date_to or ''}"
        return {
            "name": _(header),
            "type": "ir.actions.act_window",
            "view_mode": "tree",
            "res_model": "sale.person.monthly.target",
            "view_id": view_id,
            "views": [(view_id, "tree")],
            "domain": [("id", "in", res_ids.ids)],
            "target": "main",
            "context": {'create': False}
        }

    def sale_person_target_report(self, date_from, date_to):
        view_id = self.env.ref("scs_sales_person_report.sale_person_monthly_target_line_tree_view").id
        self.clear_existing_records()
        current_month_target = self.get_current_month_target(date_from, date_to)
        if not current_month_target:
            return self.no_target_found_response(view_id)

        target_lines = current_month_target.sale_person_target_line_ids

        # Get account payments and reconciled invoice IDs
        account_payments = self.get_account_payments(date_from, date_to)
        reconciled_invoice_ids = account_payments.mapped('reconciled_invoice_ids')
        # Initialize user amounts dictionary
        user_amounts = {}
        sale_order_total_amount = self.calculate_sale_order_total_amount(reconciled_invoice_ids, date_to, date_from)
        for sale_order, total_amount in sale_order_total_amount.items():
            # tax_deducted_till_now = sum(sale_order.order_line.mapped("tax_received"))
            tax_deducted = sale_order.order_line.filtered(lambda l: not l.display_type and not l.is_downpayment).get_tax_recieved_amount(sale_order,date_from, date_to, total_amount)
            cost_amount = self.get_cost_amount(sale_order, date_from, date_to, total_amount)
            # deduce the margin from the total amount only if margin exceeds paid amount
            if cost_amount > total_amount:
                # get previous payment amount
                previous_payment_amt = self.get_previous_payments(sale_order, reconciled_invoice_ids, date_to, total_amount=0.0)
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
                    if user not in user_amounts:
                        user_amounts[user] = 0.0
                    user_amounts[user] += divided_amount
            else:
                user = sale_order.user_id
                if user not in user_amounts:
                    user_amounts[user] = 0.0
                user_amounts[user] += amount_total
        # Prepare and create records in batch
        res_ids = self.create_target_lines(current_month_target, target_lines, user_amounts, date_from, date_to)
        return self.generate_report_response(res_ids, view_id, date_from, date_to)
