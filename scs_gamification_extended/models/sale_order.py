from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    gamification_data_ids = fields.One2many(
        comodel_name="sale.gamification.data",
        inverse_name="order_id",
        string="Gamification Data",
        readonly=True,
        tracking=True,
    )

    def open_gamification_wizard(self):
        return {
            "name": "Add Salesperson Parcentage",
            "type": "ir.actions.act_window",
            "res_model": "gamification.data.wizard",
            "view_mode": "form",
            "target": "new",
        }

    # @api.model_create_multi
    # def create(self, vals):
    #     records = super(SaleOrder, self).create(vals)
    #     for record in records.filtered(lambda l: l.user_id):
    #         record.write(
    #             {
    #                 "gamification_data_ids": [
    #                     (
    #                         0,
    #                         0,
    #                         {
    #                             "salesperson_id": record.user_id.id,
    #                             "percentage": 100,
    #                         },
    #                     )
    #                 ]
    #             }
    #         )
    #     return records

    # def write(self, vals):
    #     res = super().write(vals)
    #     for rec in self:
    #         if vals.get("user_id"):
    #             rec.gamification_data_ids.unlink()
    #             rec.write(
    #                 {
    #                     "gamification_data_ids": [
    #                         (
    #                             0,
    #                             0,
    #                             {
    #                                 "salesperson_id": vals.get("user_id"),
    #                                 "percentage": 100,
    #                             },
    #                         )
    #                     ]
    #                 }
    #             )
    #     return res


    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        gamification_updates = []

        for record in records.filtered(lambda l: l.user_id):
            percentage = 100 if not record.pre_salesman_user_id else 100 - int(record.pre_sales_percentage)
            gamification_updates.append((record, record.user_id.id, percentage))

        for record, user_id, percentage in gamification_updates:
            record.write({"gamification_data_ids": [(0, 0, {"salesperson_id": user_id, "percentage": percentage})]})

        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if vals.get("user_id"):
                rec.gamification_data_ids.unlink()
                rec.write(
                    {
                        "gamification_data_ids": [
                            (
                                0,
                                0,
                                {
                                    "salesperson_id": vals.get("user_id"),
                                    "percentage": 100,
                                },
                            )
                        ]
                    }
                )
            if "pre_salesman_user_id" in vals:
                gamification_updates = []
                for rec in self:
                    if rec.user_id:
                        rec.gamification_data_ids.unlink()
                        percentage = 100 if not rec.pre_salesman_user_id else 100 - int(rec.pre_sales_percentage)
                        gamification_updates.append((rec, rec.user_id.id, percentage))

                for rec, user_id, percentage in gamification_updates:
                    rec.write({"gamification_data_ids": [(0, 0, {"salesperson_id": user_id, "percentage": percentage})]})

            return res
