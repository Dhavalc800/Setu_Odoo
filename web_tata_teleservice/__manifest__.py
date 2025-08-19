# See LICENSE file for full copyright and licensing details.

{
    # Module information
    'name': 'Web Tata Teleservice',
    'version': '16.0.1.0.1',
    'category': 'Web',
    'license': 'LGPL-3',
    'summary': """
        Web Tata Teleservice
    """,

    # Author
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',

    # Dependancies
    'depends': ['web'],

    # Views
    'data': [
        'views/web_tata_teleservice.xml'
    ],

    'assets': {
        'web.assets_backend': [
            'web_tata_teleservice/static/src/xml/TataTeleServiceContainer.xml',
            'web_tata_teleservice/static/src/js/TataTeleServiceContainer.js'
        ],
     },

    # Technical
    'installable': True,
    'auto_install': False,
}
