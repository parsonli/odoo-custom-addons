# -*- coding: utf-8 -*-

{
    'name': '才用计件',
    'version': '1.0.0.0',
    'author': 'Parson Li',
    'category': 'Productivity',
    'website': 'https://www.chemi-young.com',
    'license': 'LGPL-3',
    'sequence': 3,
    'summary': """    
    
    """,
    'description': """
自制的一些辅助软件与程序
    """,
    'images': [''],
    'depends': [
                'base', 'mrp', 'hr'
    ],
    'data': [
            'security/piecework_security.xml',
            'security/ir.model.access.csv',
            'data/ir_sequence_data.xml',
            'views/piece_work.xml',
            'report/piece_work_report_views.xml',

            ],
    'qweb': [

    ],
    'demo': [],
    'test': [],
    'css': [],
    'js': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
