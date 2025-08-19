from odoo import api, models, fields, _



class QualityFeedback(models.Model):
    _name = 'quality.feedback'
    _description = 'Quality Feedback'
    _rec_name = "partner_id"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    task_id = fields.Many2one("project.task")
    project_id = fields.Many2one("project.project")
    state_name = fields.Selection(related='task_id.stage_id.state')
    partner_id = fields.Many2one("res.partner")
    customer_phone_no = fields.Char(related="partner_id.phone")
    customer_mobile_no = fields.Char(related="partner_id.mobile")
    customer_email_id = fields.Char(related="partner_id.email")
    customer_address = fields.Char(compute="_compute_address")
    survey_id = fields.Many2one(related="task_id.survey_id", string="Feedback Form")
    survey_count = fields.Integer(compute="_compute_survey_count")
    state = fields.Selection(
        [
            ("new", "New"),
            ("assign", "Assign"),
            ("confirm", "Waiting Review"),
            ("done", "Done"),
        ],
        default="new",
        string="Status",
    )
    user_ids = fields.Many2many('res.users', string="Assignee")
    is_feedback_done = fields.Boolean(compute="_compute_is_feedback_done")


    def _compute_is_feedback_done(self):
        for record in self:
            surveys = self.env['survey.user_input'].search([('task_id', '=', record.task_id.id), ('state', '=', 'done')])
            if surveys:
                record.is_feedback_done = True
                record.state = 'done'
            else:
                record.is_feedback_done = False

    def action_start_survey_from(self):
        survey = self.survey_id
        return survey.with_context(default_task_id=self.sudo().task_id.id).sudo().action_start_survey()
    
    def action_send_survey_from(self):
        survey = self.survey_id
        return survey.with_context(default_task_id=self.task_id.id, default_partner_ids= [(4, [self.partner_id.id])] ).action_send_survey()
    
    def _compute_survey_count(self):
        survey = self.env['survey.user_input'].search([('task_id', '=', self.task_id.id)])
        self.survey_count = len(survey)

    def _compute_address(self):
        for record in self:
            address_parts = [record.task_id.partner_id.street,
                             record.task_id.partner_id.street2,
                             record.task_id.partner_id.city,
                             record.task_id.partner_id.state_id.name,
                             record.task_id.partner_id.country_id.name,
                             ]
            address = ', '.join(filter(None, address_parts))
            record.customer_address = address

    def action_view_survey_result(self):
        action = self.env["ir.actions.actions"]._for_xml_id("survey.action_survey_user_input")
        survey = self.env['survey.user_input'].search([('task_id', '=', self.task_id.id)])
        if len(survey) > 1:
            action['domain'] = [('id', 'in', survey.ids)]
        elif len(survey) == 1:
            form_view = [(self.env.ref('survey.survey_user_input_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = survey.id
        return action

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        # res.get_feedback_url()
        template = self.env.ref('quality_feedback_from.mail_template_send_feedback', False)
        template.send_mail(res.id, force_send=True)
        return res
    
    def get_feedback_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        base_url += f"/web#id={self.id}&model=quality.feedback"
        return base_url