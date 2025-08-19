# See LICENSE file for full copyright and licensing details.

{
    "name": "SCS Sales Person Report",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.",
    "summary": "Sales Person Report",
    "category": "Sales Management",
    "website": "https://www.serpentcs.com",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "sale",
        "account",
        "hr",
        "sales_team_security",
    ],
    "data": [
        "security/ir.model.access.csv",
        'security/sales_collection_security.xml',
        "data/ir_cron.xml",
        "wizard/sale_person_target_wizard.xml",
        "wizard/sale_person_collection_report.xml",
        "wizard/sale_person_collection_wizard.xml",
        "views/sale_person_target_view.xml",
        "views/monthly_target_view.xml",
        "views/incentive_settlement_view.xml",
    ],
    "installable": True,
}
