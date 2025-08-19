# See LICENSE file for full copyright and licensing details.

{
    'name': 'HR Config',
    'version': '16.0.1.0.0',
    'category': 'HRMS',
    'license': 'LGPL-3',
    'summary': 'Configurations of HR',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['hr','hr_contract', 'calendar'],
    'data': [
        'security/hr_config_security.xml',
        'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/res_groups_inherited_view.xml',
        'views/hr_emp_level.xml',
        'views/hr_check_list_view.xml'
    ],
    'installable': True,
}
