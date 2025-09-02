# See LICENSE file for full copyright and licensing details.

{
    'name': 'Project -linked With Survey',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'summary': 'Project Team Management',
    'category': 'Project Management',
    'website': 'https://www.serpentcs.com',
    'version': '16.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'project', 'survey',    
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'wizard/open_survey.xml',
        'views/feedback_from_view.xml',
        'views/survey_user_view.xml',
        'views/project_project_view.xml',
        'views/project_task_view.xml',
        'views/complimentary_service_view.xml'
        
    ],
    'installable': True,
}
