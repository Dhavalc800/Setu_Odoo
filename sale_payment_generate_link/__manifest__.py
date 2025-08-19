{
    "name": "Sales Payment Link Expire",
    "summary": "This module enhances the sales payment link functionality by ensuring the link expires after a single use.",
    "version": "16.0.1.0.0",
    "category": "Sales",
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    "license": "AGPL-3",
    "installable": True,
    "depends": ['scs_sale'],
    "data": ["views/sale_portal_templates.xml"],
    "assets": {
        'web.assets_frontend': [
            'sale_payment_generate_link/static/src/js/payment.js',
        ],
    },
}
