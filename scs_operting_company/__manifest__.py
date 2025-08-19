# See LICENSE file for full copyright and licensing details.

{
    "name": "Sale Operating Company",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.",
    "summary": "Sales Team Management",
    "category": "Sales Management",
    "website": "https://www.serpentcs.com",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "sale",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/operating_company_views.xml",
        "views/res_config_settings_views.xml",
        "views/sale_order_view.xml",
        "views/account_move_view.xml",
        "views/account_payment_views.xml",
        "wizard/sale_make_invoice_advance_views.xml",
    ],
    "installable": True,
}
