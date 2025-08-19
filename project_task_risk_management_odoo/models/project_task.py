# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models, fields, _


class ProjectTasksRisk(models.Model):
    _inherit = 'project.task'

    task_risk_incident_line = fields.One2many('task.risk.incident.line',
                                              'task_incident_order_id',
                                              string='Risk Incident Lines')
    risk_incident_ids = fields.One2many('risk.incident','task_id', string='Risk Incident')
    risk_incident_count = fields.Integer(compute="compute_risk_incident", string='Risk Incident')

    def task_create_incident_wiz(self):
        return {
            'name': _('Create Incident'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'risk.incident.wiz',
            'target': 'new',
            'context': (
                {'default_user_id': self.project_id.user_id.id,
                 'default_project_id': self.project_id.id,
                 'default_task_id': self.id})
        }

    def action_view_incident(self):
        action = self.env.ref('project_task_risk_management_odoo.action_risk_incident')
        result = action.read()[0]
        result['domain'] = [('id', 'in', self.risk_incident_ids.ids)]
        return result
    
    @api.depends('risk_incident_ids')
    def compute_risk_incident(self):
        self.risk_incident_count = len(self.risk_incident_ids)


class RiskIncident(models.Model):
    _name = 'task.risk.incident.line'
    _description = "Risk Incident Line"

    task_incident_order_id = fields.Many2one('project.task', string='Risk '
                                                                    'Reference')
    risk = fields.Many2one('risks.project', string='Risk', required=True)
    des = fields.Char(string="Description")
    category = fields.Many2one('risk.category', string='Category',
                               required=True)
    risk_response = fields.Many2one('risk.response', string='Risk Response',
                                    required=True)
    risk_type = fields.Many2one('risk.type', string='Risk Type', required=True)
    probability = fields.Float(string='Probability(%)')
    tag_ids = fields.Many2many('risk.tag', string='Tags')
