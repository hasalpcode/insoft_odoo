# -*- coding: utf-8 -*-
{
    'name': "Overtime - Planning",
    'summary': """
        scheduling overtime backups
    """,
    'author': "Insoft SAS",
    'category': 'Planning',
    'version': '0.1',
    'depends': ['base', 'planning', 'base_automation'],
    'data': [
        'security/ir.model.access.csv',
        'report/details_overtime_report.xml',
        'report/overtime_report.xml',
        'data/ir_cron_data.xml',
        'data/batch.sequence.xml',
        'views/hr_department.xml',
	    'views/generate_batch_sup_hours_view.xml'
    ]
}
