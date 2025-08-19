from odoo import api,fields, models, _
from odoo.http import request
from odoo.exceptions import UserError



class SrveySurvey(models.Model):
    _inherit = "survey.user_input"

    is_negative = fields.Boolean("Negative")
    task_id = fields.Many2one("project.task")
    project_id = fields.Many2one("project.project")
    customer_id = fields.Many2one("res.partner")
    customer_email = fields.Char(related='customer_id.email')
    complimentary_service_id = fields.Many2one("complimentary.service")
    complimentary_count = fields.Integer(compute='_compute_complimentary_count')

    def create_survey_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        base_url += f"/web#id={self.id}&model=survey.user_input"
        return base_url

    @api.model_create_multi
    def create(self, vals_list):
        survey =  super(SrveySurvey, self).create(vals_list)
        for rec in survey:
            if self._context.get('default_task_id'):
                rec.write({'task_id': int(self._context.get('default_task_id'))})
        return survey
    
    def create_complimentary_service(self):
        if not self.task_id:
            raise UserError(_("Please select a task"))
        complimentary_service = self.env['complimentary.service'].create({
            'old_task_id': self.task_id.id,
            'old_project_id': self.project_id.id,
            'customer_id': self.customer_id.id
        })
        self.complimentary_service_id = complimentary_service.id
        template = self.env.ref('quality_feedback_from.mail_template_negative_review', False)
        template.send_mail(self.id)
        return True
    
    def _compute_complimentary_count(self):
        complimentary_Service = self.env['complimentary.service'].search([('id', '=', self.complimentary_service_id.id)])
        self.complimentary_count = len(complimentary_Service)

    def action_view_complimentary_service(self):
        action = self.env["ir.actions.actions"]._for_xml_id("quality_feedback_from.action_complimentary_service")
        complimentary_Service = self.env['complimentary.service'].search([('id', '=', self.complimentary_service_id.id)])
        if len(complimentary_Service) > 1:
            action['domain'] = [('id', 'in', complimentary_Service.ids)]
        elif len(complimentary_Service) == 1:
            form_view = [(self.env.ref('quality_feedback_from.complimentary_service_form_view').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = complimentary_Service.id
        return action