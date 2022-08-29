# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Air Senegal Activity Escale",
    'summary': """Activités Prestataires""",
    'description': """
    """,
    'category': 'Human Resources',
    'version': '1.0',
    'depends': ['hr','ss_ops_base','mail','base','account','snailmail_account','account_bank_statement_import',
                'account_facturx','analytic','iap','l10n_syscohada','odoo_referral','partner_autocomplete','payment','product','sms', 'snailmail'],
    'data': [
        'security/ops_activity_security.xml',
        'security/ir.model.access.csv',
        'data/ss_ops_data.xml',
        'report/ss_ops_activity_analyst_view.xml',
        'report/touchee_report.xml',
        'views/ss_ops_service_view.xml',
        'views/partner_view.xml',
        'wizard/wizard_create_service_line.xml',
        'views/ops_vol_view.xml',
        'views/res_company_view.xml',
        'report/report_bon.xml',
        'data/template_notification.xml',
        'wizard/ops_bon_sent_view.xml',




    ],
    'demo': [],
    'application': False,
    'qweb': []
}
