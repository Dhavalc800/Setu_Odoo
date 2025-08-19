from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = "account.move"

    amount_in_words = fields.Char(string="Amount in Words", compute="_compute_amount_in_words")

    @api.depends('amount_total')
    def _compute_amount_in_words(self):
        for move in self:
            move.amount_in_words = self.convert_to_indian_currency_words(move.amount_total)

    def convert_to_indian_currency_words(self, number):
        def num_to_words(n):
            units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
            teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", 
                     "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
            tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

            def two_digit(n):
                if n < 10:
                    return units[n]
                elif n < 20:
                    return teens[n - 10]
                else:
                    return tens[n // 10] + (" " + units[n % 10] if n % 10 != 0 else "")

            def three_digit(n):
                h = n // 100
                rem = n % 100
                if h and rem:
                    return units[h] + " Hundred and " + two_digit(rem)
                elif h:
                    return units[h] + " Hundred"
                else:
                    return two_digit(rem)

            output = ""
            crore = n // 10000000
            n %= 10000000
            lakh = n // 100000
            n %= 100000
            thousand = n // 1000
            n %= 1000
            hundred = n

            if crore:
                output += two_digit(crore) + " Crore "
            if lakh:
                output += two_digit(lakh) + " Lakh "
            if thousand:
                output += two_digit(thousand) + " Thousand "
            if hundred:
                output += three_digit(hundred)

            return output.strip()

        number = round(number)
        return num_to_words(int(number)) + " Rupees"

    def action_print_pro_forma_invoice(self):
        return self.env.ref("sale.action_report_pro_forma_invoice").report_action(
            self.invoice_line_ids.mapped("sale_line_ids").mapped("order_id")
        )
