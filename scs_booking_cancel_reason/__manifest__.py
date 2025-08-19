# See LICENSE file for full copyright and licensing details.

{
    'name': 'Booking Cancel Reason',
    'version': '16.0.1.0.0',
    'category': '',
    'license': 'LGPL-3',
    'summary': 'Booking Cancel Reason',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['web','sale',],
    'data': [
        'security/ir.model.access.csv',
        'wizard/cancel_wizard.xml',
        'views/cancel_reason.xml',
        'views/sale_order.xml',
        'views/export_logging_view.xml',
        ],
    'installable': True,
}
