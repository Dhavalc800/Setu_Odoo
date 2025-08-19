# See LICENSE file for full copyright and licensing details.

{
    'name': 'Project Configuration',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'category': 'Project Management',
    'version': '16.0.1.0.0',
    'license': 'LGPL-3',
    'summary': 'Project management configuration',
    'website': 'http://www.serpentcs.com',
    'description': 'Project management configuration.',
    'sequence': 1,
    'depends': ['project', 'hr_config'],
    'demo': [
        'demo/project_type_demo.xml'
    ],
    'data': [
        'data/project_data.xml',
        'security/project_security.xml',
        'security/ir.model.access.csv',
        'views/project_config_view.xml',
        'views/project_task_view.xml',
        'views/project_project_view.xml'
    ],
    'installable': True,
}
