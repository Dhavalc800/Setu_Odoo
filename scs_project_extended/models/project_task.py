from odoo import api, models, fields, _


class ProjectTasks(models.Model):
    _inherit = "project.task"

    qualification_criteria_ids = fields.One2many(
        "qualification.criteria",
        "task_id",
        string="Qualification Criteria",
    )

    active = fields.Boolean(default=True, tracking=True)

    task_imformation_ids = fields.One2many(
        "project.task.information", "task_id", string="Task Information"
    )
    state_history_ids = fields.One2many(
        "state.history", "project_task_id", string="State history")
    is_mail_send = fields.Boolean(string='Mail send',)
    is_editable = fields.Boolean("Is Editable", compute="compute_is_editable")
    can_edit = fields.Boolean("Can Edit", compute="compute_can_edit")

    related_phone = fields.Char(string='mobile', related='partner_id.mobile')
    related_email = fields.Char(string='email', related='partner_id.email')

    related_sale_price_unit = fields.Float(string='Total Amount', related="sale_line_id.price_unit")
    related_sale_note = fields.Html(string='Note', related="sale_line_id.order_id.note")
    related_sale_amt_received = fields.Monetary(string='Amount Received', related="sale_line_id.amount_received",currency_field='currency_id')
    related_sale_pending_amt = fields.Monetary(string='Booking Pending Amount', related="sale_order_id.payment_pending",currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string="Currency", related="sale_order_id.currency_id", readonly=True)
    related_sale_user_id = fields.Many2one('res.users', string="Booking Salesperson", related="sale_order_id.user_id", readonly=True)

    total_amount = fields.Float(string='Total Amount',)
    receive_amount = fields.Float(string='Amount Received',)

    draft_contract_filename = fields.Char(string="Filename", tracking=True)
    draft_contract = fields.Binary(string="Draft Document", tracking=True)

    signed_contract_filename = fields.Char(string="Filename", tracking=True)
    signed_contract = fields.Binary(string="Signed Document", tracking=True)

    remaining_amount = fields.Float(
        string="Remaining Amount",
        compute="_compute_remaining_amount",
        store=True
    )
    agreement_verified = fields.Selection(
        related="sale_line_id.order_id.agreement_id.verification_state",
        string="Agreement Verified",
        readonly=True,
        store=True
    )

    @api.depends('sale_line_id.amount_received', 'sale_line_id.price_unit')
    def _compute_remaining_amount(self):
        for task in self:
            if task.sale_line_id:
                received = task.sale_line_id.amount_received or 0.0
                total_price = task.sale_line_id.price_unit or 0.0
                task.remaining_amount = max(total_price - received, 0.0)
            else:
                task.remaining_amount = 0.0



    def compute_can_edit(self):
        for rec in self:
            rec.can_edit = (
                rec.env.user.has_group("project.group_project_manager") or rec.env.user.has_group(
                    "project_config.group_project_coordinator") or rec.env.user.has_group("project_config.group_project_manager_custom") or rec.env.user.has_group("project.group_project_user"))

    @api.depends('name')
    def compute_is_editable(self):
        for rec in self:
            rec.is_editable = (
                rec.env.user.has_group("project.group_project_manager") or rec.env.user.has_group("project_config.group_project_manager_custom")
            )

    def write(self, vals):
        state_history_obj = self.env['state.history']
        
        for rec in self:
            # DRAFT CONTRACT
            if 'draft_contract' in vals:
                if vals['draft_contract']:
                    rec.message_post(body=_("✅ Draft contract document was updated."))
                else:
                    rec.message_post(body=_("🗑️ Draft contract document was removed."))

            if 'draft_contract_filename' in vals:
                if vals['draft_contract_filename']:
                    rec.message_post(body=_("✏️ Draft contract filename changed to: <b>%s</b>") % vals['draft_contract_filename'])
                else:
                    rec.message_post(body=_("🗑️ Draft contract filename was removed."))

            # SIGNED CONTRACT
            if 'signed_contract' in vals:
                if vals['signed_contract']:
                    rec.message_post(body=_("✅ Signed contract document was updated."))
                else:
                    rec.message_post(body=_("🗑️ Signed contract document was removed."))

            if 'signed_contract_filename' in vals:
                if vals['signed_contract_filename']:
                    rec.message_post(body=_("✏️ Signed contract filename changed to: <b>%s</b>") % vals['signed_contract_filename'])
                else:
                    rec.message_post(body=_("🗑️ Signed contract filename was removed."))

        # Call original write method
        res = super().write(vals)

        for rec in self:
            # Your stage logic (optional, you can adjust as needed)
            if vals.get("stage_id") and rec.stage_id.state == "done":
                task_ids = self.search([
                    ("depend_on_ids", "in", rec.id),
                    ("stage_id", "!=", rec.stage_id.id),
                    ("id", "!=", rec.id),
                ])
                # Process task_ids if needed

            # Optional: state history tracking
            if vals.get("stage_id"):
                state_history_obj.create({
                    'project_task_id': rec.id,
                    'state': rec.stage_id.name,
                    'user': rec.env.user.id,
                    'current_state': True
                })

        return res



    # def write(self, vals):
    #     state_history_obj = self.env['state.history']
    #     res = super().write(vals)
    #     for rec in self:
    #         if vals.get("stage_id") and self.stage_id.state == "done":
    #             task_ids = self.search(
    #                 [
    #                     ("depend_on_ids", "in", self.id),
    #                     ("stage_id", "!=", self.stage_id.id),
    #                     ("id", "!=", self.id),
    #                 ]
    #             )
    #         if 'active' in vals and vals.get('active') and not rec.is_mail_send and not self._context.get('by_pass_mail'):
    #             rec.with_context(by_pass_mail=True).write({'is_mail_send': True})
    #             template = self.env.ref('scs_project_extended.mail_template_project_task', False)
    #             template.send_mail(rec.id, force_send=True)

    #     if 'stage_id' in vals:
    #         previous_substate_history = state_history_obj.search([
    #             ('order_id', '=', self.id), ('current_state', '=', True)],
    #             order="id desc", limit=1)
    #         previous_substate_history.compute_duration()
    #         previous_substate_history.current_state = False
            # state_history_obj.create({
            #     'project_task_id': self.id,
            #     'state': self.stage_id.name,
            #     'user': self.env.user.id,
            #     'current_state': True
            # })
    #     return res

    @api.model_create_multi
    def create(self, vals):
        task = super(ProjectTasks, self).create(vals)
        
        for rec in task:
            if rec.project_id:
                var = []  # ✅ Initialize var to avoid NameError
                task_var = []  # ✅ Initialize task_var as well

                if rec.project_id.qualification_criteria_ids:
                    for line in rec.project_id.qualification_criteria_ids:
                        var.append(
                            (
                                0,
                                0,
                                {
                                    "name": line.name,
                                    "releted_criteria_id": line.id,
                                    "project_id": False,
                                },
                            )
                        )

                if rec.project_id.task_imformation_ids:
                    for task_line in rec.project_id.task_imformation_ids:
                        task_var.append(
                            (
                                0,
                                0,
                                {
                                    "name": task_line.name,
                                    "type_of_field": task_line.type_of_field,
                                    "related_information_id": task_line.id,
                                    "project_id": False,
                                },
                            )
                        )

                # Assign reviewer if project has a user
                if rec.project_id.user_id:
                    rec.reviewer_id = rec.project_id.user_id.id

                # ✅ Ensure that only valid data is written to the task
                update_vals = {}
                if var:
                    update_vals["qualification_criteria_ids"] = var
                if task_var:
                    update_vals["task_imformation_ids"] = task_var

                if update_vals:
                    rec.write(update_vals)

        return task

    # @api.model_create_multi
    # def create(self, vals):
    #     task = super(ProjectTasks, self).create(vals)
    #     for rec in task:
    #         if rec.project_id:
    #             var = []
    #             task_var = []
    #             for line in rec.project_id.qualification_criteria_ids:
    #                 var.append(
    #                     (
    #                         0,
    #                         0,
    #                         {
    #                             "name": line.name,
    #                             "releted_criteria_id": line.id,
    #                             "project_id": False,
    #                         },
    #                     )
    #                 )
    #             for task_line in rec.project_id.task_imformation_ids:
    #                 task_var.append(
    #                     (
    #                         0,
    #                         0,
    #                         {
    #                             "name": task_line.name,
    #                             "type_of_field": task_line.type_of_field,
    #                             "related_information_id": task_line.id,
    #                             "project_id": False,
    #                         },
    #                     )
    #                 )
    #             # Commented code to prevent the default addition of all the team members.

    #             # if rec.project_id and rec.project_id.members_ids:
    #             #     task.update(
    #             #         {"user_ids": [(6, 0, rec.project_id.mapped("members_ids").ids)]}
    #             #     )
    #             if rec.project_id.user_id:
    #                 task.reviewer_id = rec.project_id.user_id.id

    #     task.write(
    #         {
    #             "qualification_criteria_ids": var,
    #             "task_imformation_ids": task_var,
    #         }
    #     )
    #     return task
