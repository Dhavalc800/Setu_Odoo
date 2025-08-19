# See LICENSE file for full copyright and licensing details.

{
    "name": "SCS Account Tally Report",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.",
    "summary": "SCS Account Tally Report",
    "category": "Account Management",
    "website": "https://www.serpentcs.com",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "sale",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/group.xml",
        "wizard/account_tally_report_view.xml",
        "views/account_tally_menu.xml",
    ],
    "installable": True,
}
