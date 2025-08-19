# See LICENSE file for full copyright and licensing details.

{
    'name': 'SCS CRM Extended',
    'version': '16.0.1.0.0',
    'category': 'CRM',
    'license': 'LGPL-3',
    'summary': 'CRM Extended',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['crm', 'payment', 'sales_team', 'crm_kit', 'sales_team_security'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/payment_link_wizard_views.xml',
        'views/crm_lead_pipeline_view_inherit.xml',
        'views/crm_team_process_view.xml',
        'views/product_view_inherit.xml',
    ],
    'installable': True,
}
