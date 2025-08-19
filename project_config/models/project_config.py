# See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import _, api, fields, models

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError


class ProjectPhase(models.Model):

    _name = 'project.phase'
    _description = 'Project Phase'
    _order = 'sequence'

    name = fields.Char('Name', help='The name of the Phase')
    code = fields.Char('Code', help='The code of the Phase')
    sequence = fields.Integer('Sequence', help='Sequence of the Phase')
    case_default = fields.Boolean('Default for New Projects', default=True)

    _sql_constraints = [
        ('seq_uniq', 'unique (sequence)', _("The sequence must be unique per Phase!"))
    ]


class ProjectDevelopmentModel(models.Model):

    _name = 'project.dev.model'
    _description = 'Project Model'
    # Development Model would be long term/dedicated/product
    code = fields.Char('Code', size=4,
                       help="Code for Project Development Model")
    name = fields.Char('Name', help="Project Development Model name")


class ProjectType(models.Model):
    # Type would be from the four software/erp/web/mobile app
    _name = 'project.type'
    _description = 'Project Type'

    code = fields.Char('Code', size=4, help="Code for Project Type")
    name = fields.Char('Name', help="Project Type")

class ProjectHistory(models.Model):

    _name = 'project.history'
    _description = 'Project History'

    project_id = fields.Many2one('project.project', 'Project', help="Project")
    start_date = fields.Datetime('Start Date',
                                 help="Starting Date of Project Development")
    end_date = fields.Datetime('End Date',
                               help="End Date of Project Development")
    phase_id = fields.Many2one('project.phase', 'Phase', help="Project Phase")
