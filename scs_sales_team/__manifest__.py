# See LICENSE file for full copyright and licensing details.
{
    "name": "Sales - Team Extended",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.",
    "summary": "Sales Team Extended",
    "category": "Sales Team Extended",
    "website": "https://www.serpentcs.com",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "sale",
        "sales_team",
        "sales_team_security"
    ],
    "data": [
        'security/sales_team_security.xml',
        'security/ir.model.access.csv',
        'views/sales_views.xml',
    ],
    "installable": True,
}
