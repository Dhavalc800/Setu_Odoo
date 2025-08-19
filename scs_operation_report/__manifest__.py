# See LICENSE file for full copyright and licensing details.

{
    'name': 'SCS - Operation Reports',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'summary': 'Project Team Management',
    'category': 'Project Management',
    'website': 'https://www.serpentcs.com',
    'version': '16.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'project', 'project_team', 'sale_project',
    
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/operation_activity_type.xml',
        'data/taken_days_calculate_cron.xml',
        "views/activity_types_config_view.xml",
        "views/operation_task_activity_view.xml",
        "wizard/operation_activity_wiz_view.xml",
    ],
    'installable': True,
}
