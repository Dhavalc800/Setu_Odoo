# See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import _, api, fields, models

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model
    def get_type_common(self):
        p_ids = self.env['project.phase'].search([('case_default', '=', 1)])
        return p_ids

    phase_type_ids = fields.Many2many('project.phase', 'project_phase_rel',
                                      'project_phase_id', 'phase_id',
                                      'Project Phases',
                                      default=get_type_common)
    proj_type = fields.Many2one('project.type', 'Project Type',
                                help="Choose Project Type!")
    proj_dev_id = fields.Many2one('project.dev.model', 'Project Model',
                                  help="Choose Project Development Model!")

    proj_hist_ids = fields.One2many('project.history', 'project_id',
                                    'Project History',
                                    help="Project history changes according \
                                          to project phase.",
                                    copy=False)
    phase_project_id = fields.Many2one('project.phase', 'Phase',
                                       )
    # phase_project_id = fields.Many2one('project.phase', 'Phase',
    #                                    domain="[(\
    #                                     'id', 'in', phase_type_ids)]")
        
    country_id = fields.Many2one('res.country', 
                                 string='Country')

    @api.model_create_multi
    def create(self, vals_list):
        """
        This method is used to update Project Phase History on update of Phase.
        -----------------------------------------------------------------
        @param self : object pointer
        @param vals : A dictionary containing keys and values
        @return : Recordset of the newly created record
        """
        records = super(ProjectProject, self).create(vals_list)
        ProjectHistory = self.env['project.history']
        for rec in records.filtered(lambda l:l.phase_project_id):
            ProjectHistory.create({
                'start_date': datetime.now(),
                'project_id': rec.id,
                'phase_id': rec.phase_project_id.id,
            })
        return records

    def write(self, vals):
        """
        This method is used to update Project Phase History on update of Phase.
        ------------------------------------------------------------------
        @param self : object pointer
        @param vals : A dictionary containing keys and values
        @return : True
        """
        ProjectHistory = self.env['project.history']
        res = super(ProjectProject, self).write(vals)
        for rec in self:
            if vals.get('phase_project_id', False):
                proj_st = ProjectHistory.search([
                    ('project_id', '=', rec.id),
                    ('phase_id', '=', vals['phase_project_id']),
                ])
                proj_st_end = ProjectHistory.search([
                    ('project_id', '=', rec.id),
                    ('end_date', '=', False),
                ])
                proj_st_end.write({'end_date': datetime.now()})
                if not proj_st:
                    proj_status_vals = {
                        'start_date': datetime.now(),
                        'project_id': rec.id,
                        'phase_id': vals['phase_project_id']
                    }
                    ProjectHistory.create(proj_status_vals)

        return res

    def map_tasks(self, new_project_id):
        """ restrict to copy and map tasks from old to new project """
        return True

    def _read(self, fields):
        self =self.sudo()
        return super(ProjectProject, self)._read(fields)
    
class ProjectTask(models.Model):
    _inherit = 'project.task'

    reviewer_id = fields.Many2one('res.users', 'Reviewer',
                                  tracking=True)
    task_type = fields.Selection([('develop', 'Development'),
                                  ('change', 'Change Request'),
                                  ('research_development',
                                   'Research & Development'),
                                  ('documentation', 'Documentation'),
                                  ('analysis', 'Analysis'),
                                  ('review', 'Review'),
                                  ('meeting','Meeting')],
                                 string='Task Type')
    state = fields.Selection([('draft', 'New'),
                              ('open', 'In Progress'),
                              ('pending', 'Pending'),
                              ('done', 'Done'),
                              ('cancelled', 'Cancelled')
                              ], 'State', default='draft')
    schedule_date = fields.Date(
        'Schedule Date',
        help="Date scheduled for task")


    @api.constrains('schedule_date', 'date_deadline')
    def check_end_date(self):
        """
        This method will Define a Date Dead Line  should be
        Greater than the Schedule Date.
        ---------------------------------
        @param self : object pointer
        """
        for rec in self:
            if rec.task_type != "meeting":
                if rec.date_deadline and rec.schedule_date:
                    if rec.date_deadline < rec.schedule_date:
                        raise ValidationError(_('Dead line date should be greater than schedule Date.'))

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        task_type_obj = self.env['project.task.type']
        if vals.get('stage_id', False):
            for rec in self:
                stage_rec = task_type_obj.browse(vals.get('stage_id'))
                if stage_rec:
                    rec.state = stage_rec.state
        return res

    def unlink(self):
        """ Delete the Task and it's related analytic account line. """
        for project_task in self:
            flage = True
            if project_task.stage_id.name in \
                    ['Done', 'In Progress', 'Testing', 'Advanced']:
                raise UserError(_("You can not Delete %s Task.") %
                                project_task.stage_id.name)
            elif project_task.timesheet_ids:
                for timesheet_line in project_task.timesheet_ids:
                    if timesheet_line.sheet_id and \
                        timesheet_line.sheet_id.state in \
                            ['confirm', 'done']:
                        flage = False
                        raise UserError(
                            _("You can not Delete Task."))
                if flage:
                    for timesheet_line in project_task.timesheet_ids:
                        timesheet_line.unlink()
        return super(ProjectTask, self).unlink()

    def name_get(self):
        """
        Overridden name_get method to display Task ID and Task Name in the
        Many2one field
        ------------------------------------------------------------------
        @param self : object pointer
        """
        self= self.sudo()
        res = []
        for task in self:
            task_str = "[" + str(task.id) + "]" + task.name
            res.append((task.id, task_str))
        return res

    @api.model
    def name_search(self, name='', args=[], operator='ilike', limit=100):
        """
        Overridden name_search method to to search by Task ID and Task Name in
        the Many2one field
        -----------------------------------------------------------------------
        @param self : object pointer
        """
        new_args = []
        if name:
            new_args = []
            try:
                new_args = ['|',('name', operator, name), ('id', '=', int(name))]
            except:
                new_args = [('name', operator, name)]
            args += new_args
        tasks = self.search(args)
        return tasks.name_get()


class ProjectTaskAnalysis(models.Model):

    _inherit = 'report.project.task.user'

    date_deadline = fields.Datetime('Deadline', readonly=True)


class ProjectTaskType(models.Model):

    _inherit = 'project.task.type'

    state = fields.Selection([('draft', 'New'),
                              ('open', 'In Progress'),
                              ('pending', 'Pending'),
                              ('done', 'Done'),
                              ('cancelled', 'Cancelled')
                              ], 'State',
                             copy=False,
                             help="Process of Task.")
