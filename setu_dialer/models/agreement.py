from odoo import models, fields, api

class Agreement(models.Model):
    _inherit = "agreement"

    product_ids = fields.Many2many('product.product', string="Products", compute="_compute_product_ids", store=True)
    stage = fields.Selection([
            ('call_verified', 'Call and Verified'),
            ('not_pick', 'Not Pick/Busy'),
            ('not_eligible', 'Not Eligible'),
            ('no_action', 'No Action Required'),
        ], string="Stage", default=False)
    assign_id = fields.Many2one('res.users', string="Assigned To", tracking=True)
    agreement_status = fields.Selection([
            ('recived', 'Agreement Recived'),
            ('not_recived', 'Aggreement Not Recived'),
            ('urgent_attention', 'Urgent Attention'),
            ('process_hold', 'Process Hold'),
            ('refund_case', 'Refund Case'),
            ('having_concern', 'Having Concern'),
            ('Ack Done', 'Ack Done'),
        ], string="Agreement Status", default='not_recived', tracking=True, help="Status of the agreement")

    def action_agreement_feedback_wizard(self):
        """ Open wizard to set feedback user on agreement """
        return {
            'name': 'Set Feedback User',
            'type': 'ir.actions.act_window',
            'res_model': 'agreement.feedback.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_agreement_ids': [(6, 0, self.ids)],
                'active_ids': self.ids,
                'active_model': 'agreement.feedback.wizard',
            },
        }

    # def action_activate_agreement_projects(self):
    #     for rec in self:
    #         if rec.stage_id and rec.stage_id.is_active:
    #             # Activate main project
    #             if rec.sale_id.project_id and not rec.sale_id.project_id.active:
    #                 rec.sale_id.project_id.active = True
    #             # Activate multiple projects if any
    #             if rec.sale_id.project_ids:
    #                 rec.sale_id.project_ids.write({'active': True})
    #             # Activate project from line's sale line
    #             if rec.line_ids:
    #                 sale_lines = rec.line_ids.mapped('sale_line_id')
    #                 if sale_lines:
    #                     # Activate line projects
    #                     sale_lines.mapped('project_id').write({'active': True})
    #                     # Only load tasks if they exist
    #                     if any(sl.task_id for sl in sale_lines):
    #                         sale_lines.mapped('task_id.project_id').write({'active': True})
 
    # def action_activate_agreement_projects(self):
    #     for rec in self:
    #         if rec.stage_id and rec.stage_id.is_active:
    #             # Activate main project
    #             if rec.sale_id.project_id and not rec.sale_id.project_id.active:
    #                 rec.sale_id.project_id.active = True
    #             # Activate multiple projects if any
    #             if rec.sale_id.project_ids:
    #                 rec.sale_id.project_ids.write({'active': True})
    #                 print("\n\n\n000000000000000000")
    #             # Activate project from line's sale line
    #             if rec.line_ids and rec.line_ids.mapped('sale_line_id.project_id'):
    #                 rec.line_ids.mapped('sale_line_id.project_id').write({'active': True})
    #                 print("\n\n\n111111111111111111")
    #             # Activate project from task if present
    #             if rec.line_ids and rec.line_ids.mapped('sale_line_id.task_id.project_id'):
    #                 rec.line_ids.mapped('sale_line_id.task_id.project_id').write({'active': True})
    #                 print("\n\n\nRecccccccccccc", rec)

    @api.depends('line_ids.product_id')
    def _compute_product_ids(self):
        for record in self:
            record.product_ids = record.line_ids.mapped('product_id')
    
    def action_send_welcome_email(self):
        self.ensure_one()
        template = self.env.ref('setu_dialer.mail_template_welcome_agreement', raise_if_not_found=False)
        ctx = {
            'default_model': 'agreement',
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template.id if template else None,
            'default_composition_mode': 'comment',
            'force_email': True,
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'ctx': {
                'client_name': self.partner_id.name or '',
                'company_name': self.partner_id.name or '',
                'mobile': self.partner_id.mobile or '',
                'email': self.partner_id.email or '',
                'services': 'Grant, Loan, and Investment',
                    'payment_summary': 'Your payment summary will be provided soon.',
            }
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def action_send_not_pick_email(self):
        self.ensure_one()
        template = self.env.ref('setu_dialer.mail_template_not_pick_agreement', raise_if_not_found=False)
        ctx = {
            'default_model': 'agreement',
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template.id if template else None,
            'default_composition_mode': 'comment',
            'force_email': True,
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'ctx': {
                'client_name': self.partner_id.name or '',
                'company_name': self.partner_id.name or '',
                'mobile': self.partner_id.mobile or '',
                'email': self.partner_id.email or '',
                'services': 'Grant, Loan, and Investment',
                'payment_summary': 'Your payment summary will be provided soon.',
            }
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }