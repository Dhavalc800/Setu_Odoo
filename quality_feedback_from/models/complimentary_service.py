from odoo import api, models, fields, _


class ComplimentaryService(models.Model):
    _name = 'complimentary.service'
    _description = 'Complimentary Service'
    _rec_name = "customer_id"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    old_task_id = fields.Many2one("project.task", required=True)
    old_project_id = fields.Many2one("project.project")
    assignee = fields.Many2one(related='old_project_id.user_id')
    complimentary_project_id = fields.Many2one("project.project")
    complimentary_task_id = fields.Many2one("project.task")
    customer_id = fields.Many2one("res.partner")
    customer_phone_no = fields.Char(related="customer_id.phone")
    customer_mobile_no = fields.Char(related="customer_id.mobile")
    customer_email_id = fields.Char(related="customer_id.email")
    customer_address = fields.Char(compute="_compute_address")
    state = fields.Selection(
        [
            ("new", "New"),
            ("approve", "Approve"),
            ("reject", "Reject"),
        ],
        default="new",
        string="Status",
    )
    complimentary_services_count = fields.Integer(compute='compute_complimentary_services')
    is_confirm = fields.Boolean()

    @api.depends('customer_id')
    def _compute_address(self):
        for record in self:
            address_parts = [record.customer_id.street,
                             record.customer_id.street2,
                             record.customer_id.city,
                             record.customer_id.state_id.name,
                             record.customer_id.country_id.name,
                             ]
            address = ', '.join(filter(None, address_parts))
            record.customer_address = address

    def action_approve(self):
        self.state = 'approve'

    def action_reject(self):
        self.state = 'reject'   

    def action_confirm(self):
        name = [self.customer_id.name,
                self.complimentary_project_id.name]
        name = ', '.join(filter(None, name))
        self.is_confirm = True
        task_vals =             {
                "name": name,
                "complimentary_service": True,
                "sale_line_id": self.old_task_id.sale_line_id.id if self.old_task_id and self.old_task_id.sale_line_id else False,
            }

        task = self.env['project.task'].create(task_vals)
        self.complimentary_task_id = task.id

    def compute_complimentary_services(self):
        complimentary_services = self.env['project.task'].search([('id', '=', self.complimentary_task_id.id)])
        self.complimentary_services_count = len(complimentary_services)     

    def action_view_complimentary_services(self):
        action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_task")
        complimentary_services = self.env['project.task'].search([('id', '=', self.complimentary_task_id.id)])
        if len(complimentary_services) > 1:
            action['domain'] = [('id', 'in', complimentary_services.ids)]
        elif len(complimentary_services) == 1:
            form_view = [(self.env.ref('project.view_task_form2').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = complimentary_services.id
        return action