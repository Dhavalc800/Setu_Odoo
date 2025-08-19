# See LICENSE file for full copyright and licensing details.

{
    'name': 'Gamification - Extended',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'summary': 'Gamification process',
    'category': 'Human Resources',
    'website': 'https://www.serpentcs.com',
    'version': '16.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'sale', 'gamification','scs_pre_salesperson'

    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'wizard/gamification_data_wizard_view.xml'

    ],
    'installable': True,
}
