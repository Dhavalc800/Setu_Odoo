# See LICENSE file for full copyright and licensing details.

{
    'name': 'Project - Extended',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'summary': 'Project Team Management',
    'category': 'Project Management',
    'website': 'https://www.serpentcs.com',
    'version': '16.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'project', 'project_team', 'sale_project', "project_config", 'scs_sale','agreement_reports',
    
    ],
    'data': [
        'data/task_mail_template.xml',
        'security/ir.model.access.csv',
        'security/project_security.xml',
        'wizard/view_project_task_assignees.xml',
        'views/project_project_view.xml',
        'views/project_task_view.xml',
        'views/crm_team_view.xml',
        "views/product_view.xml",
        "views/sale_order_view.xml",
        "views/project_portal_view.xml",
        "views/employee_branch_view.xml"
    ],
    
    "assets": {
        "web.assets_backend": [
            "scs_project_extended/static/src/js/form_controller.js",
        ],
    },
    'installable': True,
}
