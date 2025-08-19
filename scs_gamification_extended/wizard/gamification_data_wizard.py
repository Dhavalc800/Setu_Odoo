from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GamificationDataWizard(models.TransientModel):
    _name = "gamification.data.wizard"
    _description = "Add Sale Person Percentage"

    sale_gamification_ids = fields.One2many(
        "sale.gamification.data.wizard", "wizard_id", string="Add Saleperson"
    )
    salesperson_ids = fields.Many2many("res.users", compute="compute_sales_person")

    @api.depends("sale_gamification_ids", "sale_gamification_ids.salesperson_id")
    def compute_sales_person(self):
        self.salesperson_ids = [
            (6, 0, self.sale_gamification_ids.mapped("salesperson_id").ids)
        ]

    def add_percentage(self):
        sale_order = self.env["sale.order"].browse(self._context.get("active_id"))
        data = []
        wiz_salesperson_percentage = sum(
            [round(record.percentage, 2) for record in self.sale_gamification_ids]
        )
        has_negative_percentage = any(
            record.percentage < 0 for record in self.sale_gamification_ids
        )
        if has_negative_percentage:
            raise UserError(_("You can not add Salesperson percentage in nagative %"))
        if wiz_salesperson_percentage > 100:
            raise UserError(_("You can not add Salesperson percentage more then 100 %"))
        wiz_salesperson = self.sale_gamification_ids.mapped("salesperson_id")
        unlink_record = sale_order.gamification_data_ids.filtered(
            lambda l: l.salesperson_id not in wiz_salesperson
        )
        unlink_record.unlink()

        for line in self.sale_gamification_ids:
            if not sale_order.gamification_data_ids:
                data.append(
                    (
                        0,
                        0,
                        {
                            "salesperson_id": line.salesperson_id.id,
                            "percentage": line.percentage,
                        },
                    )
                )
            else:
                if line.salesperson_id not in sale_order.gamification_data_ids.mapped(
                    "salesperson_id"
                ):
                    data.append(
                        (
                            0,
                            0,
                            {
                                "salesperson_id": line.salesperson_id.id,
                                "percentage": line.percentage,
                            },
                        )
                    )
                else:
                    for sol_line in sale_order.gamification_data_ids.filtered(
                        lambda l: l.salesperson_id == line.salesperson_id
                    ):
                        sol_line.write({"percentage": line.percentage})
        sale_order.write({"gamification_data_ids": data})

    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        sale_order = self.env["sale.order"].browse(self._context.get("active_id"))
        data = []
        if sale_order.gamification_data_ids:
            for line in sale_order.gamification_data_ids:
                data.append(
                    (
                        0,
                        0,
                        {
                            "salesperson_id": line.salesperson_id,
                            "percentage": line.percentage,
                        },
                    )
                )
            defaults.update({"sale_gamification_ids": data})
        else:
            defaults.update(
                {
                    "sale_gamification_ids": [
                        (
                            0,
                            0,
                            {"salesperson_id": sale_order.user_id, "percentage": 100},
                        )
                    ]
                }
            )
        return defaults

    # @api.onchange("sale_gamification_ids", "sale_gamification_ids.salesperson_id")
    # def onchange_percentage(self):
    #     if self.sale_gamification_ids:

    #         def split_float_almost_equally(n_parts):
    #             base_value = 100 // n_parts
    #             remainder = 100 % n_parts

    #             result = [base_value] * n_parts

    #             for i in range(int(remainder)):
    #                 result[i] += 1
    #             return result

    #         split = split_float_almost_equally(len(self.sale_gamification_ids))
    #         count = 0
    #         for line in self.sale_gamification_ids:
    #             line.percentage = split[count]
    #             count += 1

    @api.onchange("sale_gamification_ids", "sale_gamification_ids.salesperson_id")
    def onchange_percentage(self):
        if self.sale_gamification_ids:
            active_model = self._context.get('active_model')
            active_id = self._context.get('active_id')
            base_value = 100
            if active_model == 'sale.order' and active_id:
                sale_order = self.env['sale.order'].browse(active_id)
                if sale_order.pre_salesman_user_id and sale_order.pre_sales_percentage:
                    base_value = 100 - sale_order.pre_sales_percentage

            n_parts = len(self.sale_gamification_ids)

            def split_float_almost_equally(n_parts, base_value):
                base_value = base_value // n_parts
                remainder = base_value % n_parts
                result = [base_value] * n_parts
                for i in range(int(remainder)):
                    result[i] += 1
                return result

            split = split_float_almost_equally(n_parts, base_value)
            for count, line in enumerate(self.sale_gamification_ids):
                line.percentage = split[count]
