# See LICENSE file for full copyright and licensing details.

{
    'name': 'Pre-SalesPerson',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'summary': 'Pre-SalesPerson',
    'category': 'Sales',
    'website': 'https://www.serpentcs.com',
    'version': '16.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/pre_sales_wizard_view.xml',
        "views/sale_order_view.xml",
        "views/res_config_setting_view.xml",
    ],
    'installable': True,
}
