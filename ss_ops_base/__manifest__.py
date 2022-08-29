# -*- encoding: utf-8 -*-

{
    'name': 'Module base',
    'summary': 'Base profils',
    'version': '12.0.1.0',
    'category': 'Base',
    'summary': """
""",
    'author': "M Y Diallo",
    'website': '',
    'license': 'LGPL-3',
    'images': [],
    'depends': ['base','mail','account','hr'],
	'website':[],
    'data': [

        'security/si_air_senegal_security.xml',
        'security/ir.model.access.csv',
        'data/ss_ops_data.xml',
        'views/menu_items.xml'
    ],
    'installable': True,
    'application': False,
}
