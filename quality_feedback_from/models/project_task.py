from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)

class ProjectTasks(models.Model):
    _inherit = 'project.task'
    
    survey_id = fields.Many2one("survey.survey", string="Feedback Form")
    feedback_ids = fields.One2many("quality.feedback", 'task_id', string="Feedback")
    feedback_count = fields.Integer(compute = "_compute_feedback_count")
    complimentary_task_id = fields.Many2one("project.task")
    complimentary_task_count = fields.Integer(compute='compute_complimentary_task_count')
    complimentary_service = fields.Boolean()

    @api.model_create_multi
    def create(self, vals):
        task = super(ProjectTasks, self).create(vals)
        for rec in task:
            if rec.project_id and rec.project_id.survey_id:
                task.survey_id = rec.project_id.survey_id.id
            if self._context.get('project_id'):
                task.project_id = self._context.get('project_id')
                task.partner_id = self._context.get('customer_id')
            if self._context.get('task_id'):
                parent = self.search([('id', '=', self._context.get('task_id'))])
                parent.write({'complimentary_task_id': task.id})
                task.parent_id = parent.id
        return task
    
    def write(self, vals):
        if vals.get('state') == 'done':
            self.create_feedback_request()
            # template = self.env.ref('quality_feedback_from.mail_template_send_feedback', False)
            # template.send_mail(feedback.id)
        return super().write(vals)
    
    # def get_feedback_url(self, feedback):
    #     base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
    #     base_url += f"/web#id={feedback.id}&model=quality.feedback"
    #     return base_url
    
    def create_feedback_request(self):
        feedback = self.env['quality.feedback'].create({
            'partner_id': self.partner_id.id,
            'task_id': self.id,
            'project_id': self.project_id.id,
            'user_ids': self.project_id.feedback_user_id
        })
        # url = self.get_feedback_url(feedback)
        
        
        # feedback.message_post(body=partner_message,
        #                       message_type= 'email',
        #                       partner_ids=feedback.user_ids.ids)
        # template = self.env.ref('project.mail_template_data_project_task', False)
        # template.send_mail(self.id)
        # # partner_message = "A new feedback request has been created for task ID {}".format(self.id)
        # self.message_post(body=partner_message)
        self.feedback_ids = [(6, 0, feedback.id)]
        return self.feedback_ids
        

    def _compute_feedback_count(self):
        feedback = self.env['quality.feedback'].search([('task_id', '=', self.feedback_ids.task_id.id),
                                                        ('project_id', '=', self.project_id.id)])
        self.feedback_count = len(feedback)


    def action_view_feedback(self):
        action = self.env["ir.actions.actions"]._for_xml_id("quality_feedback_from.action_quality_feedback")
        feedback = self.env['quality.feedback'].search([('task_id', '=', self.feedback_ids.task_id.id),
                                                        ('project_id', '=', self.project_id.id)])
        if len(feedback) > 1:
            action['domain'] = [('id', 'in', feedback.ids)]
        elif len(feedback) == 1:
            form_view = [(self.env.ref('quality_feedback_from.quality_feedback_form_view').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = feedback.id
        return action
    
    def compute_complimentary_task_count(self):
        complimentary_task = self.search([('id', '=', self.complimentary_task_id.id)])
        self.complimentary_task_count = len(complimentary_task)
    
    def action_view_complimentary_task(self):
        action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_task")
        if self.complimentary_task_id:
            complimentary_task = self.search([('id', '=', self.complimentary_task_id.id)])
        else:
            complimentary_task = self.search([('id', '=', self.parent_id.id)])
            
        if len(complimentary_task) > 1:
            action['domain'] = [('id', 'in', complimentary_task.ids)]
        elif len(complimentary_task) == 1:
            form_view = [(self.env.ref('project.view_task_form2').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = complimentary_task.id
        return action

    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self._context.get("feedback"):
            _logger.info("Feedback context detected. Adding stage filter to args.")
            args = args + [('stage_id.state', '=', 'done')]
        _logger.debug("Search args: %s", args)
        _logger.debug("Offset: %s, Limit: %s, Order: %s, Count: %s, UID: %s", offset, limit, order, count, access_rights_uid)
        return super()._search(args, offset, limit, order, count, access_rights_uid)

    # def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
    #     if self._context.get("feedback"):
    #         args = args + [('stage_id.state', '=', 'done')]
    #     return super()._search(args, offset, limit, order, count, access_rights_uid)