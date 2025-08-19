# See LICENSE file for full copyright and licensing details.

{
    "name": "Sales - Extended",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.",
    "summary": "Sales Team Management",
    "category": "Sales Management",
    "website": "https://www.serpentcs.com",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        'base_substate',
        "sale",
        "account",
        "contacts",
        "l10n_in_tcs_tds",
        "scs_operting_company",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/sale_security.xml",
        "data/data.xml",
        "views/sale_report.xml",
        "views/sale_order_view.xml",
        "views/sale_portal_templates.xml",
        "views/paper_format.xml",
        "views/payment_plan_view.xml",
        "views/partner_view.xml",
        "views/industry_sector.xml",
        # "views/server_action.xml",
        "views/pro_form_invoice_report.xml",
        "views/base_substate_view.xml",
        "views/payment_link_wizard.xml",
    ],
    'assets': {
        'web.report_assets_common': [
            'scs_sale/static/img/qr_setu_serv.png',
        ],
    },

    "installable": True,
}
