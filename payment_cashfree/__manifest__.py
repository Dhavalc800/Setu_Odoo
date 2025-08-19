# -*- coding: utf-8 -*-

{
    'name': "Payment Cashfree",
    'summary': """Payment Acquirer: Cashfree Implementation""",
    'description': """Payment Acquirer: Cashfree Implementation""",
    'category': 'Payment Acquirer',

    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'company': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com/',

    'version': '16.0.1.0.0',
    'license': 'OPL-1',
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_cashfree_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_cashfree/static/src/**/*',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',

}
