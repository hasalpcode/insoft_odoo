# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Air Senegal Planning",
    'summary': """Manage your employees' schedule""",
    'description': """
    Schedule your teams and employees with shift.
    """,
    'category': 'Human Resources/Planning',
    'version': '1.0',
    'depends': ['hr', 'web_gantt','base','mail','operating_unit',
    'hr','ss_ops_base','mail','base','account','snailmail_account'],
    'data': [
        'security/planning_security.xml',
        'security/ir.model.access.csv',
	    'report/report_planning_preview.xml',
        'report/report_planning_sup_hours.xml',
        'data/mail_data.xml',
        'wizard/planning_send_views.xml',
        'views/assets.xml',
        'views/planning_template_views.xml',
        'views/planning_views.xml',
        'views/res_config_settings_views.xml',
        'views/planning_templates.xml',
        'data/planning_cron.xml',
        'views/hr_views.xml',
        'views/planning_preview_view.xml',
        'wizard/wizard_planning_repeat_view.xml',
        #'report/planning_report_views.xml',
        'wizard/wizard_generate_sup_hours_view.xml',
        'views/planning_sup_hours_view.xml',
        'views/planning_period_view.xml'

    ],
    'demo': [
        'data/planning_demo.xml',
    ],
    'application': False,
    'qweb': [
        'static/src/xml/planning_gantt.xml',
        'static/src/xml/field_colorpicker.xml',
    ]
}
