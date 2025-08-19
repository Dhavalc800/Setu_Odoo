from odoo import api, fields, models


class ActivityTypeConfig(models.Model):
    _name = "activity.type.config"
    _description = "Activity Type Config"

    company_id = fields.Many2one("res.company")
    name = fields.Char("Reference")
    project_ids = fields.Many2many("project.project", string="Projects")

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        op_task_act_ids = self.env["project.task"].browse(
            [self._context.get("task_id")]
        )
        activity_type_ids = self.search(
            [("project_ids", "in", [op_task_act_ids.project_id.id])]
        )
        new_args = []
        if activity_type_ids:
            new_args = []
            try:
                new_args = [("id", "in", activity_type_ids.ids)]
            except:
                new_args = args
            # return super()._name_search(
            #     name="", args=new_args, operator="ilike", limit=100, name_get_uid=None
            # )
            return super(ActivityTypeConfig, self)._name_search(name=name, args=new_args, operator=operator, limit=limit,
                                                            name_get_uid=name_get_uid)

        elif self._context.get("skip_context"):
            return super(ActivityTypeConfig, self)._name_search(name=name, args=args, operator=operator, limit=limit,
                                                        name_get_uid=name_get_uid)
        else:
            return new_args
