# See LICENSE file for full copyright and licensing details.

{
    'name': 'data migration',
    'version': '16.0.1.0.0',
    'category': '',
    'license': 'LGPL-3',
    'summary': 'Data migration',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['sale','base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/datafile.xml',
        'views/menuitem.xml',
        ],
    'installable': True,
}
