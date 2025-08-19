# See LICENSE file for full copyright and licensing details.

{
    'name': 'Project Timesheets',
    'version': '16.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Project Management',
    'summary': 'Project Timesheets',
    'description': """
       Synchronization of timesheet entries with project task work entries.
        ====================================================================
        This module lets you transfer Timesheet line entries to the
        entries under tasks defined for Project Management for
        particular date and particular user with the effect of creating,
        editing and deleting either ways. """,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['hr_timesheet', 'project_config'],
    'data': [
        'security/ir.model.access.csv',
        'security/project_timesheet_security.xml',
        'views/project_timesheet_view.xml',
        'views/hr_timesheet_type_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
