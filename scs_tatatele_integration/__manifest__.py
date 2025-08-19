# See LICENSE file for full copyright and licensing details.

{
    'name': 'Tata Tele service Integration',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'summary': 'Tata Teleservice Integration',
    'category': 'Integration',
    'website': 'https://www.serpentcs.com',
    'version': '16.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'base', 'web', 'crm','queue_job', 'sales_team_security', 'hr',

    ],
    'data': [
        'security/tatatele_security.xml',
        'security/ir.model.access.csv',
        'data/multiple_user_fetch_data.xml',
        'wizard/fetch_lead_wizard_view.xml',
        'wizard/user_token_view.xml',
        'views/broadcast_list_view.xml',
        'views/lead_details_view.xml',
        'views/res_user_view_inherit.xml',
        'views/call_records_details_view.xml',
        'views/crm_lead_view_inherit.xml',
        'views/campaign_views.xml',
        'views/tatatele_menu.xml',
    ],
    'assets': {
        "web.assets_backend": [
            "/scs_tatatele_integration/static/src/lib/audio_field.js",
            "/scs_tatatele_integration/static/src/xml/widget.xml",]
    },
    'images': ['static/description/icon.png'],
    'installable': True,
}
