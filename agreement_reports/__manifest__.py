# See LICENSE file for full copyright and licensing details.

{
    'name': 'Agreement Report',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'summary': 'All Reports',
    'category': 'reports',
    'website': 'https://www.serpentcs.com',
    'version': '16.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'agreement_legal_sale', "scs_operting_company"
    ],
    'data': [
        # 'data/demo_agreement.xml',
        # 'data/agreement_data.xml',
        'data/agreement_mail_template.xml',
        'security/ir.model.access.csv',
        'views/agreement_view.xml',
        # 'views/product_template_view.xml',
        "views/sale_order_view.xml",
        "views/agreement_stage_view.xml",
        'reports/agreement_report_template.xml',
        'reports/agreement_report.xml',
    ],
    'installable': True,
}
