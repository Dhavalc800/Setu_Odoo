{
    'name': 'Smart Biometric Sync',
    'version': '16.0',
    'summary': 'Sync attendance data from biometric device using JSON-RPC',
    'sequence': 10,
    'author': 'Your Name',
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        # 'security/ir.model.access.csv',
        'data/ir_cron_data.xml',  # Ensure this line is present
        'views/biometric_sync_views.xml',
        'views/res_config_setting.xml',
    ],
    'installable': True,
    'application': True,
}