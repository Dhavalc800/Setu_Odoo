# -*- coding: utf-8 -*-

{
    'name': "Maintenance  - Extended",
    'summary': """Maintenance""",
    'description': """Maintenance""",
    'category': 'Maintenance',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'company': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com/',
    'version': '16.0.1.0.0',
    'license': "AGPL-3",
    'depends': ['maintenance'],
    'data': [
        'security/maintenance_security.xml',
        'security/ir.model.access.csv',
        'views/maintenance_views.xml'],
    'installable': True,
}
